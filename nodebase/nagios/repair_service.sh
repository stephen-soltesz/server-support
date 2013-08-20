#!/usr/bin/env bash

#########################################################################
# repair_service.sh
#    Closes the loop for Nagios service repairs
#    Invoked remotely via NRPE.
# 
#    Distributed by ConfFiles:
#        from boot: PlanetLabConf/mlab/repair_service_sh 
#          to node: /usr/lib/nagios/plugins/repair_service.sh
#       started by: nrpe daemon on node.
#       depends on: /etc/sudoers
#########################################################################

if [[ -z "$1" && -z "$2" ]] ; then
    echo "Error: requires two arguments: $0 slicename servicename"
    exit 1
fi

## NOTE: some machines get into a weird state where 'vserver slice exec'
## fails, while 'su - slice' works.  While this shouldn't happen, it does, and
## 'vserver_exec' is an attempt to work around it.
## 
function vserver_exec () {
    slice=$1
    cmd=$2
    ## sudo    -- to let the nrpe user run 'su'.
    ## su      -- to enter the sliver as the slice user.
    ## sudo -s -- to enter 'root' within the context.
    sudo /bin/su - $slice <<EOF
sudo -s <<XXX
    $cmd
XXX
EOF
}

## NOTE: this works for "root" user also.
function root_exec () {
    vserver_exec "root" "$1"
}


## TODO: include disk quota repairs and log deletions.

## NOTE: exec_and_send <slicename> <service> <action-str> <execute> <commands>
##       <slicename> -- the slicename to operate on. should be a valid slice.
##       <service>   -- the name of the service.  can be any str.
##       <action>    -- word describing action. i.e. 'repair, restart', etc.
##       <execute>   -- how to execute <commands>.  i.e. vserver, root, testing, etc.
##                      only, 'root' and 'vserver' are executed.  Everythign
##                      else is treated as a 'testing' mode.
##       <commands>  -- the commands to run to restore the slice.

function exec_and_send () {
    local slicename=$1
    local service=$2
    local action=$3
    local execute=$4
    local commands=$5

    echo slicename: $slicename
    echo service  : $service
    echo action   : $action
    echo exec     : $execute
    echo cmds     : $commands

    local s0=$( echo $slicename | sed -e 's/.*_//g' )
    local s1=$( echo $slicename | sed -e 's/_.*//g' )
    local host=`hostname | sed -e 's/.measurement-lab.org//g' `
    local hostlink=${s0}.${s1}.$( hostname )
    local prefix=""

    case $execute in 
        vserver|root)
            prefix=""
            ;;
        *)
            ## NOTE: if 'execute' not specified then it's just a test message
            prefix="(TESTING) "
            ;;
    esac

    local subject="${prefix}$action $service on $slicename@$host"
    local nagios_url="http://ks.measurementlab.net/nagiosRepairMail.php"

    MESSAGE="${prefix}Repair Service: $action $service on $slicename@$host\n"
    MESSAGE+="Check the service status here:\n"
    MESSAGE+="    http://nagios.measurementlab.net/nagios/cgi-bin/status.cgi?host=$hostlink\n\n"
    case $execute in 
        vserver|root)
            case $execute in 
                vserver)
                    ret=$( vserver_exec "$slicename" "$commands" )
                ;;
                root)
                    ret=$( root_exec "$commands" )
                ;;
            esac
            MESSAGE+="We just ran the command:\n"
            MESSAGE+="    $commands\n"
            MESSAGE+="Returned:\n"
            MESSAGE+="    $ret\n"
            echo "ret: $ret"
            ;;
        *)
            MESSAGE+="We could have used this command, but did nothing:\n"
            MESSAGE+="    $commands\n"
            ;;
    esac

    ## NOTE: test should return "OK"
    local result=$( curl -s --form dryrun=1 $nagios_url )
    if [ "$result" != "OK" ] ; then
        echo "Cannot send to nagios. Mail gateway not working."
        echo "expected 'OK', returned: $result"
        return 1
    fi
    ## NOTE: add "--form debug=1 for more messages.
    ## NOTE: read upload message from stdin to nagios-url.
    echo -e "$MESSAGE" | curl -s --form subject="$subject" --form message=@- $nagios_url
    echo "sent message to nagios ok"
    return 0
}

SLICENAME=$1
SERVICENAME=$2

if [ "$SERVICENAME" = "disk" ] ; then
    ## NOTE: exec_and_send slicename service action-str execute-context commands

    ## NOTE: this command takes longer than 60-seconds to execute.  This is
    ##       the limit for NRPE commands.  Send it to background.
    exec_and_send "$SLICENAME" "$SERVICENAME" "repair" "root" "
        bash -c '/etc/cron.daily/delete_logs_safely.py -s $SLICENAME --until-nonzero-delete >> /tmp/nrpe_delete_safely.log < /dev/null &'; "
    ## No further action is needed.
    exit 0
fi


## NOTE: How to add a new repair command:
##
##   Given a SLICENAME that runs a service, 
##         a SERVICENAME as used by nagios,
##         a set of COMMANDS to run that will restore the service,
##         and, a CONTEXT in which to run the COMMANDS, 
##   You can create a repair entry below.
##
##   The basic pattern is:
##      SLICENAME)
##           SERVICENAME)
##                 execute in CONTEXT COMMANDS
##
##   Here context is either 'vserver', 'root', or other, where other takes
##   no action. This is useful for testing a new entry before taking it 
##   live.
##  
##   The output from commands will be sent to all the email addresses listed
##   in root@ks:/usr/local/etc/nagios/service_restart_contact_list.txt


case $SLICENAME in 
    gt_bismark)
        case $SERVICENAME in 
            *)
                exec_and_send "$SLICENAME" "$SERVICENAME" "repair" "vserver-testing" "
                    /etc/init.d/bismark-mserver reload "
            ;;
        esac
        ;;
    princeton_namecast)
        case $SERVICENAME in
            dns)
                exec_and_send "$SLICENAME" "$SERVICENAME" "repair" "vserver-testing" "
                    bash -c 'cd /home/princeton_namecast/; ./nupctl.sh restart MLAB MYSQL '"
                ;;
        esac
        ;;
 
    mpisws_broadband|gt_partha|mlab_neubot|iupui_ndt|iupui_npad|michigan_1|mlab_pipeline)
        exec_and_send "$SLICENAME" "$SERVICENAME" "repair" "vserver" "service slicectrl restart"
        ;;
    *)
        # others are either not defined.
        exec_and_send $SLICENAME "$SERVICENAME" "undefined" "vserver-testing" "    No known restart command for $SLICENAME $SERVICENAME"
        ;;
esac

echo "Restart for $SERVICENAME in $SLICENAME@`hostname` `date`"
