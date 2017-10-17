from __future__ import print_function
import logging
import os
import sys
import json


logging.basicConfig(filename='/tmp/mmcentrify.log',level=logging.DEBUG)
LOG = logging.getLogger(__name__)

# Workaround to allow testing
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

try:
    from mmcentrify import centrify as centrify
except ImportError as e:
    LOG.error("Import error!")
    LOG.debug('%s', e)


if __name__ == "__main__":
    # Read the configuration
    with open('testconfig.json') as f:
        _testconfig = json.load(f)

    centrify_tenant=_testconfig['centrify_tenant']
    centrify_user=_testconfig['centrify_user']
    centrify_password=_testconfig['centrify_password']

    default_user=_testconfig['default_user']
    default_role1=_testconfig['default_role1']
    default_role2=_testconfig['default_role2']

    # Check arguments to determine user nad role
    if len(sys.argv) != 3:
        LOG.info('Arguments not provided! Using default!')
        user = default_user
        role1 = default_role1
        role2 = default_role2
    else:
        user = sys.argv[1]
        role1 = sys.argv[2]
        role2 = sys.argv[3]

    if(centrify_tenant == '') or (centrify_user == '') or (centrify_password == ''):
        raise RuntimeError('Cannot read Centrify Tenant and and User/Password from configuration')

    # Centrify Endpoint information
    centrifytarget = {
        'tenant' :  centrify_tenant,
        'token' : None
    }

    # Test atomic functions

    token = centrify.authenticate(centrifytarget, centrify_user, centrify_password)
    LOG.info('Authenticated against Centrify API for Tenant %s with user %s, got token %s' % (centrify_tenant, centrify_user, token))

    centrifytarget['token'] = token

    userid = centrify.lookup_user(centrifytarget, user)
    LOG.info('Looked up user Centrify ID %s from user name %s' % (userid, user))

    roleid1 = centrify.lookup_role(centrifytarget, role1)
    LOG.info('Looked up role Centrify ID %s from role name %s' % (roleid1, role1))

    roleid2 = centrify.lookup_role(centrifytarget, role2)
    LOG.info('Looked up role Centrify ID %s from role name %s' % (roleid2, role2))

    centrify.add_user_to_role(centrifytarget, userid, roleid1)
    LOG.info('Added user %s (Centrify ID %s) to role %s (Centrify ID %s)' % (user, userid, role1, roleid1))

    centrify.remove_user_from_role(centrifytarget, userid, roleid2)
    LOG.info('Removed user %s (Centrify ID %s) from role%s (Centrify ID %s)' % (user, userid, role2, roleid2))

    # Test added functions
    #centrify.lookup_and_add(centrifytarget, user, role1)
    #LOG.info('Looked up and added user %s to role %s' % (user, role1))

    #centrify.lookup_and_remove(centrifyarget, user, role2)
    #LOG.info('Looked up and removed user %s from role %s' % (user, role2))

    LOG.info('All tests were successful!')

    print('All tests were successful!')
    exit()

