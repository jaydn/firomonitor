import subprocess
import datetime
import shlex
import json
import time
import sys
import os

sys.path.append(os.path.abspath('/shared'))
from sendmail import send_status_change_alert,send_score_increase_alert,send_reward_alert
from models import User, Node, State, create_schema
from znconfig import config
from zcoin import ZCoinAdapter


x = config['node_args']
z = ZCoinAdapter(x['host'], x['port'], x['user'], x['password'])

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

def znode_list():
    '''
        evoznodelist
        ---------
        proTxHash
        address
        payee
        status
        lastpaidtime
        lastpaidblock
        owneraddress
        votingaddress
        collateraladdress
        pubkeyoperator

        protx list registered true
        ---------
        proTxHash
        collateralHash
        collateralIndex
        collateralAddress
        operatorReward
        state
        confirmations
        wallet
        service
        registeredHeight
        lastPaidHeight
        PoSePenalty
        PoSeRevivedHeight
        PoSeBanHeight
        revocationReason
        ownerAddress
        votingAddress
        payoutAddress
        pubKeyOperator

    '''
    combined_list = {}

    evoznodelist = z.call('evoznodelist')
    combined_list = {k.replace('COutPoint', '').strip('()\r\n'): v for k,v in evoznodelist.items()}

    protx_list = z.call('protx', 'list', 'registered', 'true')
    for _ in protx_list:
        for k,v in _.items():
            try:
                combined_list[f"{_['collateralHash']}, {_['collateralIndex']}"][k] = v
            except Exception as e:
                log.error(f"Choked on {k}: {v} ({str(e)})")
                continue

    return combined_list

#znode_list()

def is_synced():
    obj = z.call('evoznsync', 'status')
    return 'AssetID' in obj and obj['AssetID'] == 999

def main():
    should_send_mail = config["should_send_mail"]
    if not is_synced():
        log.error('List is not synced (AssetID != 999)')
        return

    cache = znode_list()

    all_nodes = Node.select()

    status_alerts = []
    pose_score_alerts = []
    winner_alerts = []

    for node in all_nodes:
#        print(node.txid)
        try:
            node_result = cache[node.txid]
            #print(str(node_result))
        except:
            node_result = {}
        
        should_alert_status = False
        should_alert_pose_score = False
        should_alert_winner = False

        old_status = node.node_status
        if node_result.get('status', 'NOT_ON_LIST') != old_status and old_status != None:
            should_alert_status = True
#            print('{2} : {1} -> {0}'.format(node_result[NODE_STATUS], node.node_status, node.user.email))
    
        node.node_collat_addr     = node_result.get('collateralAddress', None)
        node.node_status          = node_result.get('status', 'NOT_ON_LIST')
        
        old_pose_score = node.node_pose_score
        node.node_pose_score      = node_result.get('state', {}).get('PoSePenalty', None)
        try:
            if int(old_pose_score) < int(node.node_pose_score):
                should_alert_pose_score = True
        except Exception as e:
            pass # for pose scores of none

        old_last_paid_block = node.node_last_paid_block
        node.node_last_paid_block = node_result.get('lastpaidblock', None)
        try:
            if old_last_paid_block != None:
                if int(old_last_paid_block) < int(node.node_last_paid_block):
                    if node.user.reward_emails:
                        should_alert_winner = True
                    else:
                        log.debug("Alert emails turned off")
                else:
                    log.debug("Last paid block not newer than old entry " + str(old_last_paid_block) + str(node.node_last_paid_block))
            else:
                log.debug("Old last paid time is None")
        except Exception as e:
            log.error("Error when checking last paid "+str(e))
            pass
        
        node.node_ip              = node_result.get('state', {}).get('service', None)
        node.node_last_paid_time  = None if node_result.get('lastpaidtime', 0) == 0 else datetime.datetime.fromtimestamp(int(node_result['lastpaidtime']))
        node.node_last_paid_block = node_result.get('lastpaidblock', None)
        node.node_payout_addr     = node_result.get('state', {}).get('payoutAddress', None)
        node.node_owner_addr      = node_result.get('state', {}).get('ownerAddress', None)
        node.node_voting_addr     = node_result.get('state', {}).get('votingAddress', None)
        node.node_protx_hash      = node_result.get('proTxHash', None)
        node.node_oper_pubkey     = node_result.get('state', {}).get('pubKeyOperator', None)
        node.node_oper_reward     = node_result.get('operatorReward')
        
        node.save()

        if should_alert_status:
            status_alerts.append((node, old_status))
        
        if should_alert_pose_score and not should_alert_status:
            pose_score_alerts.append((node, old_pose_score))

        if should_alert_winner:
            winner_alerts.append((node,))

    log.info('Processed {0} nodes, sending {1} status emails {2} pose score emails {3} rewards emails'.format(len(all_nodes), len(status_alerts), len(pose_score_alerts), len(winner_alerts)))

    for alert in status_alerts:
        if should_send_mail:
            send_status_change_alert(*alert)
        else:
            log.info('Would have sent status change email if mail not disabled')
        log.info(*alert)

    for alert in pose_score_alerts:
        if should_send_mail:
            send_score_increase_alert(*alert)
        else:
            log.info('Would have sent PoSe score threshold alert email if mail not disabled')
        log.info(*alert)

    for alert in winner_alerts:
        if should_send_mail:
            send_reward_alert(*alert)
        else:
            log.info('Would have sent reward email if mail not disabled')
        log.info(*alert)





if __name__ == '__main__':
    while True:
        try:
            log.info('starting loop ' + str(datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')))
            main()
            log.info('ending loop ' + str(datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')))

            last = State.select().where(State.key == 'last_updated').first()
            last.value = int(time.time())
            last.save()

            time.sleep(10)
        except Exception as e:
            try:
                create_schema()
            except Exception as ee: #  almost always already exists
                log.error(str(ee))
            log.error(str(e))
            time.sleep(5)
