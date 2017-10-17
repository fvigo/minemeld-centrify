import requests
import json
import getpass
import sys
import time

# Set the request parameters
centrify_tenant = "AAT0209"
url_auth_start = '/Security/StartAuthentication'
url_auth_advance = '/Security/AdvanceAuthentication'
poll_delay = 5 # polling delay in seconds
max_retries = 12 # max numbers of polls

tenanthost = centrify_tenant + '.my.centrify.com'

# Check arguments
if len(sys.argv) != 3:
	print "Usage: " + sys.argv[0] + " <user> <password>"
	sys.exit(1)

user = sys.argv[1]
password = sys.argv[2]

print 'Trying to authenticate user ' + user + ' with password $$$$$'

# Set proper headers
headers = {"Content-Type":"application/json","X-CENTRIFY-NATIVE-CLIENT":"True" }



################# Start Authentication


# Start Authentication
url = "https://" +  tenanthost + url_auth_start
req = {}
req['TenantId'] = centrify_tenant
req['User'] = user;
req['Version'] = '1.0'

print 'Invoking URL %s for user %s start authentication ' % ( url, user )

response = requests.post(url, headers=headers, data = json.dumps(req) )

# Check for HTTP codes other than 200
if response.status_code != 200:
    print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
    exit()

print 'Sent StartAuthentication for ' + user + '!'

# Decode the JSON response into a dictionary and use the data
data = json.loads(response.text)

print 'JSON response to StartAuthentication is %s:\n' % json.dumps(data, indent=4, sort_keys=True)

if data['success'] != True:
    raise Exception('Exception: Success is false')

result = data['Result']
if result['Summary'] != 'NewPackage':
    raise Exception('Unexpected Summary Response: %s (expected NewPackage)' % result['Summary'])

sessionid = result['SessionId']

print 'MFA Required for authentication, with SessionID %s' % sessionid

print 'There are %d available challenges for MFA' % len(result['Challenges'])

ch = []
for c in result['Challenges']:
    ch.append(c)
    print 'Challenge (%d mechanisms) [type/name/id]:' % len(c['Mechanisms'])
    for m in c['Mechanisms']:
        print '\t' + m['AnswerType'] + '\t' + m['Name'] + '\t' + m['MechanismId']


# Save Challenges and Mechanisms (assume two challenges and one mechanism per challenge for this PoC)
m0 = ch[0]['Mechanisms'][0]
m1 = ch[1]['Mechanisms'][0]
if m0['Name'] != 'UP':
    raise Exception('Expected first Challenge to be named UP, found %s instead' % m0['Name'])

if m1['Name'] != 'OTP':
    raise Exception('Expected second Challenge to be named OTP, found %s instead' % m1['Name'])


# Now Proceed with Password authentication



#################### Advance Authentication with Password


# Advance Authentication with Password

# Advance Authentication
url = "https://" +  tenanthost + url_auth_advance
req = {}
req['TenantId'] = centrify_tenant
req['MechanismId'] = m0['MechanismId']
req['Action'] = 'Answer'
req['Answer'] = password
req['SessionId'] = sessionid


print 'Invoking URL %s for user %s advance authentication ' % ( url, user )

response = requests.post(url, headers=headers, data = json.dumps(req) )

# Check for HTTP codes other than 200
if response.status_code != 200:
    print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
    exit()

print 'Sent AdvanceAuthentication for ' + user + '!'

# Decode the JSON response into a dictionary and use the data
data = json.loads(response.text)

print 'JSON response to AdvanceAuthentication is %s:\n' % json.dumps(data, indent=4, sort_keys=True)

if data['success'] != True:
    raise Exception('Exception: Success is false')

result = data['Result']
if result['Summary'] != 'StartNextChallenge':
    raise Exception('Unexpected Summary Response: %s (expected StartNextChallenge)' % result['Summary'])


#################### Advance Authentication OOB


# Advance Authentication OOB

# OOB Advance Authentication
url = "https://" +  tenanthost + url_auth_advance
req = {}
req['TenantId'] = centrify_tenant
req['MechanismId'] = m1['MechanismId']
req['Action'] = 'StartOOB'
req['SessionId'] = sessionid


print 'Invoking URL %s for user %s OOB advance authentication ' % ( url, user )

response = requests.post(url, headers=headers, data = json.dumps(req) )

# Check for HTTP codes other than 200
if response.status_code != 200:
    print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
    exit()

print 'Sent OOB AdvanceAuthentication for ' + user + '!'

# Decode the JSON response into a dictionary and use the data
data = json.loads(response.text)

#print 'JSON response to OOB AdvanceAuthentication is %s:\n' % json.dumps(data, indent=4, sort_keys=True)

if data['success'] != True:
    raise Exception('Exception: Success is false')

result = data['Result']
if result['Summary'] != 'OobPending':
    raise Exception('Unexpected Summary Response: %s (expected OobPending)' % result['Summary'])



#################### Keep polling until positive response or max retries


# Poll OOB

# Poll OOB
url = "https://" +  tenanthost + url_auth_advance
req = {}
req['TenantId'] = centrify_tenant
req['MechanismId'] = m1['MechanismId']
req['Action'] = 'Poll'
req['SessionId'] = sessionid

retries = 0
while retries < max_retries:
    print 'Invoking URL %s for polling status of user %s OOB advance authentication (%d/%d)' % ( url, user, retries, max_retries )

    response = requests.post(url, headers=headers, data = json.dumps(req) )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
        exit()

    print 'Polled OOB AdvanceAuthentication for ' + user + '!'

    # Decode the JSON response into a dictionary and use the data
    data = json.loads(response.text)

    #print 'JSON response to Polling on OOB AdvanceAuthentication is %s:\n' % json.dumps(data, indent=4, sort_keys=True)

    if data['success'] != True:
        raise Exception('Exception: Success is false')

    result = data['Result']

    if result['Summary'] == 'LoginSuccess':
        print 'Authentication Successful for user %s!' % user
        break

    # If not LoginSuccess or OobPending or previous error, something wrong is happening
    if result['Summary'] != 'OobPending':
        raise Exception('Unexpected Summary Response: %s (expected OobPending)' % result['Summary'])

    retries+=1
    time.sleep(poll_delay)

# END
