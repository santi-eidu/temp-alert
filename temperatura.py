import requests
import os
import git

TOKEN_URL = 'https://api.honeywell.com/oauth2/accesstoken'

def get_access_token(client_id, client_secret):
  response = requests.post(
      TOKEN_URL,
      data={"grant_type": "client_credentials"},
      auth=(client_id, client_secret),
  )
  return response.json()["access_token"]

def get_location(location_url, client_id, token, userid):
  locations = []
  headers = {
    "Authorization": "Bearer "+token,
    "UserRefID": userid
    }

  response = requests.get(
      location_url+"?apikey="+client_id,
      headers=headers
  )

  for location in response.json():
    locations.append(location["locationID"])

  return locations[0]

def get_device(device_url, client_id, token, userid, locationid):
  headers = {
    "Authorization": "Bearer "+token,
    "UserRefID": userid
    }

  response = requests.get(
      device_url+"?apikey="+client_id+"&locationId="+str(locationid),
      headers=headers
  )

  for device in response.json():
    if device["name"] == "Mi termostato":
      return device["deviceID"]

  return 0

def get_temperature(temperature_url, client_id, token, userid, locationid, deviceid):
  headers = {
    "Authorization": "Bearer "+token,
    "UserRefID": userid
    }

  response = requests.get(
      temperature_url+deviceid+"?apikey="+client_id+"&locationId="+str(locationid),
      headers=headers
  )

  return response.json()["indoorTemperature"]

def change_state(state, gh_token):
  repo_url = "github.com/santi-eidu/temp-alert.git"
  repo = git.Repo.clone_from("https://"+repo_url, "./repo-tmp", branch="main")
  repo.git.checkout('--orphan', 'state-branch')
  repo.git.rm('-rf', ".")
  with open('./repo-tmp/state', 'w') as f:
    if state == 1:
      f.write("0")
    elif state == 0:
      f.write("1")

  repo.index.add(['state'])
  repo.index.commit("Create storage")
  repo.git.push("https://"+gh_token+"@"+repo_url, "--force")

def ntfy(topicid, temperature, state, gh_token):
  
  headers = {
    "Title": "Cambio de temperatura"
  }

  if temperature <= 21 and state == 0:
    body = "Ha bajado la temperatura a "+str(temperature)
    change_state(state, gh_token)
    requests.post(
      "https://ntfy.sh/"+topicid,
      data=body,
      headers=headers
    )
  elif temperature > 22 and state == 1:
    body = "Ha subido la temperatura a "+str(temperature)
    change_state(state, gh_token)
    requests.post(
      "https://ntfy.sh/"+topicid,
      data=body,
      headers=headers
    )

def main():

  client_id = os.environ['client_id']
  client_secret = os.environ['client_secret']
  userid = os.environ['userid']
  topic = os.environ['topic']
  gh_token = os.environ['GITHUB_TOKEN']

  token = get_access_token(client_id, client_secret)
  location = get_location("https://api.honeywell.com/v2/locations", client_id, token, userid)
  device = get_device("https://api.honeywell.com/v2/devices", client_id, token, userid, location)
  temperature = get_temperature("https://api.honeywell.com/v2/devices/thermostats/", client_id, token, userid, location, device)

  state = requests.get("https://raw.githubusercontent.com/santi-eidu/temp-alert/state-branch/state")

  ntfy(topic, temperature, state.json(), gh_token)

if __name__ == '__main__':
    main()
