import msal
import requests
import asyncio
import webbrowser
import json
from datetime import datetime
from msal import PublicClientApplication

application_id = "" # REQUIRED : The ID of the application registration listed in Azure.
base_url = 'https://graph.microsoft.com/v1.0/'
authority_url = 'https://login.microsoftonline.com/44444-4444-4444-44444' # Makes auth easier just linking the tenant ID in the authority URL. You can use the common one but update this and compile.
# authority_url = 'https://login.microsoftonline.com/common'
scope = ['User.Read', 'RoleManagement.ReadWrite.Directory'] # REQUIRED : The permissions you'll need to give to your app registration in Azure.

class graph_initialize():
    headers: str = ""
    refresh_token: str = ""
    user_id: str = ""
    
    def __init__(self):
        return
    
    def __del__(self):
        print("...Disconnect...")

    # New method to auth.
    def get_auth(self) -> dict:
        result = None
        self.app =  PublicClientApplication(
            application_id,
            authority=authority_url
        )
        claims = {
            "access_token": {
                "acrs": {
                "essential": True,
                "value": "c1"
                }
            }
        }
        claims = json.dumps(claims)
        try:
            result = self.app.acquire_token_interactive(scopes=scope, claims_challenge=claims)
            # result = result.json()
            access_token_id = result['access_token']
            self.headers = {'Authorization': 'Bearer ' + access_token_id}
            # print(result)
            b = {"Status": "Checkout success", "Error": ""}
            b['Error'] = "Token aquired without issue"
            return(b)
        except Exception as e:
            a = {"Status": "Token failed", "Error": ""}
            a['Error'] = e
            return(a)
        
    def get_flow(self):
        self.app =  PublicClientApplication(
            application_id,
            authority=authority_url
        )
        self.flow = self.app.initiate_device_flow(scopes=scope)
        # self.flow = self.app.initiate_auth_code_flow(claims_challenge="")
        return(self.flow)

    async def get_token(self, uri: str):
        webbrowser.open(uri)
        claims = {
            "access_token": {
                "acrs": {
                "essential": True,
                "value": "c1"
                }
            }
        }
        claims = json.dumps(claims)
        try:
            result = self.app.acquire_token_by_device_flow(flow=self.flow, claims_challenge=claims)
            self.app.get_authorization_request_url
            print(result)
            access_token_id = result['access_token']
            self.headers = {'Authorization': 'Bearer ' + access_token_id}
            print(self.headers)
            return("Token success")
        except Exception as e:
            print(e)
            return("Token failed")
        
    def get_personaldata(self) -> str:
        if self.user_id != "":
            return self.user_id
        endpoint = base_url + 'me'
        response = requests.get(endpoint, headers=self.headers)
        self.user_id = response.json()
        # print(self.user_id)
        return(self.user_id)

    def get_roles(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = base_url + f"roleManagement/directory/roleEligibilitySchedules?$filter=principalId eq '{d['id']}'&$expand=roleDefinition"
            response = requests.get(endpoint, headers=self.headers)
            self.allroles = response
            return(response.json())
    
    def get_active_roles(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = base_url + f"roleManagement/directory/roleAssignmentSchedules?$filter=principalId+eq+'{d['id']}'&$expand=roleDefinition "
            response = requests.get(endpoint, headers=self.headers)
            # self.allroles = response
            return(response.json())
        
    def checkout_roles(self, role: str) -> dict:
        # date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        d = self.get_personaldata()
        role_list = self.allroles.json()
        for i in role_list['value']:
            if i['roleDefinition']['displayName'] == role:
                # print(f"Match: {i['roleDefinition']['displayName']} and {role}")
                # print(i['roleDefinitionId'])
                a = i
                
        body = {
            "action": "selfActivate",
            "PrincipalId": "",
            "Justification": "Needed for work.",
            "RoleDefinitionId": "",
            "DirectoryScopeId": "",
            "scheduleInfo": {
                "StartDateTime": "2025-06-25T14:30:00Z",
                "Expiration": {
                    "Type": "AfterDuration",
                    "Duration": ""
                }
            }
        }
        body['PrincipalId'] = d['id']
        body['RoleDefinitionId'] = a['roleDefinitionId']
        body['DirectoryScopeId'] = a['directoryScopeId']
        body['scheduleInfo']['Expiration']['Duration'] = "PT8H"
        
        try:
            endpoint = base_url + f"roleManagement/directory/roleAssignmentScheduleRequests"
            response = requests.post(endpoint, headers=self.headers, json=body)
            t = response.json()
            if t['error']['message'] == "The following policy rules failed: [\"ExpirationRule\"]":
                print("Trying 4 hours.")
                body['scheduleInfo']['Expiration']['Duration'] = "PT4H"

                endpoint = base_url + f"roleManagement/directory/roleAssignmentScheduleRequests"
                response = requests.post(endpoint, headers=self.headers, json=body)
                t = response.json()
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
            elif t['error']['code'] == "BadRequest":
                a = {"Status": "Checkout Failed", "Error": ""}
                a['Error'] = "Checkout Failed due to BadRequest. Try acquiring a new token"
                return(a)
            else:
                # print(t)
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
        except Exception as e:
            a = {"Status": "Checkout Succeeded", "Error": ""}
            a['Error'] = "Chekcout succeeded without issue"
            return(a)
