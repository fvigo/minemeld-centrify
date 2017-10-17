import logging
import requests
import json
import re
import sys

LOG = logging.getLogger(__name__)

# Object/Function Name for debugging purposes in log
# If this is invoked within an object, then it will be self.name, otherwise the function name
try:
  self
except NameError:
    MYNAME = sys._getframe().f_code.co_name
else:
    MYNAME = self.name
    

# Centrify URIs
url_userlookup = '/UserMgmt/GetUserAttributes'
url_rolelookup = '/Redrock/query'
url_rolechange = '/Roles/UpdateRole'
url_auth_start = '/Security/StartAuthentication'
url_auth_advance = '/Security/AdvanceAuthentication'

# Authenticate against API
def authenticate(centrifytarget, user, password):
    tenanthost = '{}.my.centrify.com'.format(centrifytarget['tenant'])

    LOG.debug('{} - Authenticating on API with user {} !'.format(MYNAME, user))

    # Set proper headers
    headers = {"Content-Type":"application/json","X-CENTRIFY-NATIVE-CLIENT":"True" }

    # Start Authentication
    url = "https://" +  tenanthost + url_auth_start
    req = {}
    req['TenantId'] = centrifytarget['tenant']
    req['User'] = user;
    req['Version'] = '1.0'

    LOG.debug('{} - Invoking URL {} for start authentication'.format(MYNAME, url))
    
    response = requests.post(url, headers=headers, data = json.dumps(req) )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise RuntimeError('{} - StartAuthentication API Error! Status: {} Headers: {} Error Response: {}'.format(MYNAME, response.status_code, response.headers,response.json()))

    LOG.debug('{} - Sent StartAuthentication for user {} !'.format(MYNAME, user))
    
    # Decode the JSON response into a dictionary and use the data
    data = json.loads(response.text)

    LOG.debug('{} - JSON response to StartAuthentication is {}'.format(MYNAME,json.dumps(data, indent=4, sort_keys=True)))

    if data['success'] != True:
        raise RuntimeError('{} - API Error! \'success\' is not true!'.format(MYNAME))

    result = data['Result']
    if result['Summary'] != 'NewPackage':
        raise RuntimeError('{} - StartAuthentication: Unexpected Summary Response: {} (expected NewPackage)'.format(MYNAME, result['Summary']))

    sessionid = result['SessionId']

    LOG.debug('{} - There are {} available challanges for Authentication'.format(MYNAME,len(result['Challenges'])))

    ch = []
    for c in result['Challenges']:
        ch.append(c)
        LOG.debug('{} - Challenge ({} mechanisms) [type/name/id]:'.format(MYNAME,len(c['Mechanisms'])))
        for m in c['Mechanisms']:
            LOG.debug('{} -     {}    {}    {}'.format(MYNAME,m['AnswerType'],m['Name'],m['MechanismId']))

    m0 = ch[0]['Mechanisms'][0]
    if m0['Name'] != 'UP':
        raise RuntimeError('{} - StartAuthentication: Expected firt Challanged to be \'UP\', found {} instead'.format(MYNAME, m0['Name']))

    # Now Proceed with Password authentication

    # Advance Authentication
    url = "https://" +  tenanthost + url_auth_advance
    req = {}
    req['TenantId'] = centrifytarget['tenant']
    req['MechanismId'] = m0['MechanismId']
    req['Action'] = 'Answer'
    req['Answer'] = password
    req['SessionId'] = sessionid


    LOG.debug('{} - Invoking URL {} for advance authentication'.format(MYNAME, url))

    response = requests.post(url, headers=headers, data = json.dumps(req) )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise RuntimeError('{} - AdvanceAuthentication API Error! Status: {} Headers: {} Error Response: {}'.format(MYNAME, response.status_code, response.headers,response.json()))

    LOG.debug('{} - Sent AdvanceAuthentication for user {} !'.format(MYNAME, user))

    # Decode the JSON response into a dictionary and use the data
    data = json.loads(response.text)

    LOG.debug('{} - JSON response to AdvanceAuthentication is {}'.format(MYNAME,json.dumps(data, indent=4, sort_keys=True)))

    if data['success'] != True:
        raise RuntimeError('{} - API Error! \'success\' is not true!'.format(MYNAME))

    result = data['Result']
    if result['Summary'] != 'LoginSuccess':
        raise RuntimeError('{} - AdvanceAuthentication: Unexpected Summary Response: {} (expected LoginSuccess)'.format(MYNAME, result['Summary']))

    LOG.debug('{} - API Authentication Successful for User {} - Auth Headers {}'.format(MYNAME,user, dict(response.cookies)))
    return response.cookies

# Looks up an Centrify user ID and Status from username
def lookup_user(centrifytarget, user):
    tenanthost = '{}.my.centrify.com'.format(centrifytarget['tenant'])
        
    url = 'https://{}{}'.format(tenanthost, url_userlookup)

    LOG.debug('{} - Invoking URL {} for user lookup'.format(MYNAME, url))

    # Set proper headers
    headers = {"Content-Type":"application/json","X-CENTRIFY-NATIVE-CLIENT":"True" }

    req = {}
    req['ID'] = user
    if(centrifytarget['token']):
        cookies = centrifytarget['token']

    LOG.debug('{} - Request: {}'.format(MYNAME,json.dumps(req)))
    response = requests.post(url, headers=headers, data = json.dumps(req), cookies=cookies )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise RuntimeError('{} - API Error! Status: {} Headers: {} Error Response: {}'.format(MYNAME, response.status_code, response.headers,response.json()))

    LOG.debug('{} - Performed user lookup for user {} !'.format(MYNAME, user))

    # Decode the JSON response into a dictionary and use the data
    data = response.json()
    LOG.debug('{} - user lookup data is: {}'.format(MYNAME, json.dumps(data)))

    if not data['success']:
        raise RuntimeError('{} - API Error! \'success\' is not true!'.format(MYNAME))
    
    u = data['Result']['Uuid']

    LOG.debug('{} - User {} Centrify UUID is: {}'.format(MYNAME, user, u))

    return u


# Look up a Centrify Role ID from the role name
def lookup_role(centrifytarget, role):
    tenanthost = '{}.my.centrify.com'.format(centrifytarget['tenant'])
        
    url = 'https://{}{}'.format(tenanthost, url_rolelookup)

    LOG.debug('{} - Invoking URL {} for role lookup'.format(MYNAME, url))

    # Set proper headers
    headers = {"Content-Type":"application/json","X-CENTRIFY-NATIVE-CLIENT":"True" }

    req = {}
    req['Script'] = 'SELECT * from Role WHERE ID = \'{}\' ORDER BY ID COLLATE NOCASE'.format(role)
    if(centrifytarget['token']):
        cookies = centrifytarget['token']

    LOG.debug('{} - Request: {}'.format(MYNAME,json.dumps(req)))
    response = requests.post(url, headers=headers, data = json.dumps(req), cookies=cookies )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise RuntimeError('{} - API Error! Status: {} Headers: {} Error Response: {}'.format(MYNAME, response.status_code, response.headers,response.json()))

    LOG.debug('{} - Performed role lookup for role {} !'.format(MYNAME, role))

    # Decode the JSON response into a dictionary and use the data
    data = response.json()
    LOG.debug('{} - role lookup data is: {}'.format(MYNAME, json.dumps(data, indent=4, sort_keys=True)))

    if not data['success']:
        raise RuntimeError('{} - API Error! \'success\' is not true!'.format(MYNAME))
    
    count = data['Result']['Count']
    if(count != 1):
        raise RuntimeError('{} - API Error! Result count is {} instead of 1'.format(MYNAME, count))

    roleid = data['Result']['Results'][0]['Row']['ID']

    LOG.debug('{} - Role {} Centrify ID is: {}'.format(MYNAME, role, roleid))

    return roleid


# Adds or Delete a user to a Centrify Role
# Inputs are userid and role ID in Centrify format
def update_role(centrifytarget, action, userid, roleid):
    tenanthost = '{}.my.centrify.com'.format(centrifytarget['tenant'])
        
    url = 'https://{}{}'.format(tenanthost, url_rolechange)

    LOG.debug('{} - Invoking URL {} for role update'.format(MYNAME, url))

    # Set proper headers
    headers = {"Content-Type":"application/json","X-CENTRIFY-NATIVE-CLIENT":"True" }

    req = {}
    req['Name'] = roleid
    act = { action : [ userid ] }
    req['Users'] = act
    if(centrifytarget['token']):
        cookies = centrifytarget['token']

    LOG.debug('{} - Request: {}'.format(MYNAME,json.dumps(req)))
    response = requests.post(url, headers=headers, data = json.dumps(req), cookies=cookies )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise RuntimeError('{} - API Error! Status: {} Headers: {} Error Response: {}'.format(MYNAME, response.status_code, response.headers,response.json()))

    LOG.debug('{} - Performed {} of user {} on role {} !'.format(MYNAME, action, userid, roleid))

    # Decode the JSON response into a dictionary and use the data
    data = response.json()
    LOG.debug('{} - role update data is: {}'.format(MYNAME, json.dumps(data, indent=4, sort_keys=True)))

    if not data['success']:
        raise RuntimeError('{} - API Error! \'success\' is not true!'.format(MYNAME))
    
    LOG.debug('{} - Performed {} of user {} on role {}!'.format(MYNAME, action, userid, roleid))

# Add an Centrify user to an Centrify Role
# Inputs are userid and role ID in Centrify format
def add_user_to_role(centrifytarget, userid, roleid):
    update_role(centrifytarget, 'Add', userid, roleid)

# Remove an Centrify user from an Centrify role
# Inputs are userid and role ID in Centrify format
def remove_user_from_role(centrifytarget, userid, roleid):
    update_role(centrifytarget, 'Delete', userid, roleid)

# Look up user and role and add user to role
def lookup_and_add(centrifytarget, user, role):
    add_user_to_role(centrifytarget, lookup_user(centrifytarget, user), lookup_role(centrifytarget, role))

# Look up user and role and remove user from role
def lookup_and_remove(centrifytarget, user, role):
    remove_user_from_role(centrifytarget, lookup_user(centrifytarget, user), lookup_group(centrifytarget, role))
