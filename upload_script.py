import os
import json
import requests 
import sys
import getpass
import shutil
import os.path
import zipfile
import platform
 
 
def getSep():
    if platform.system() == "Darwin":
        return '/'
    elif platform.system() == "Windows":
        return '\\'
    elif platform.system() == "Mac OS":
        return '/'
    elif platform.system() == "Unix":
        return '/'
print getSep()
 

# HARD CODED STUFF USER WILL NEED TO CHANGE
scratch = "C:" + getSep() + "users" + getSep() + getpass.getuser() + getSep()+ "Desktop" + getSep() + "tmp"
exr_writer = "C:" + getSep() + "users" + getSep() + getpass.getuser() + getSep()+ ".nuke" + getSep() + "company_name" + getSep() + "artist_nuke_submit_EXRs.nk"

 
#Gets the API key from the user
def getAPIkey():
    user = os.path.expanduser("~")
    user = user + getSep() + "AppData\\Local\\Thorax" + getSep()
    
 
    config = user + 'artist_config.json'
    
 
    if os.path.exists(user):
        print "this directory exists. moving on!"
    else:
        os.makedirs(user)
        print "created " + user
 
    
 
    if os.path.exists(config):
 
         with open(config) as i:
            data = json.load(i)
         
            return data['api_key']
 
    else:
 
        p = nuke.Panel('api key')
        p.addSingleLineInput('enter your api key', '')
        ret = p.show()
        api = p.value()
 
        with open(config, 'w') as jsonFile:
 
            empty_json =  '{}' 
            api_lib = {"api_key":api} 
            api_json_object = json.loads(empty_json) 
            api_json_object.update(api_lib) 
            json.dump(api_json_object, jsonFile)
            jsonFile.close()
            print "api key stored!"
 
print getAPIkey()
 
#GETS INFO ABOUT THE CURRENT ARTIST FROM THE ONLINE DATABASE
def getInfo(api):
    data = {'api_key': api}
    url = 'company api url'
    session = requests.Session()
    r = session.post(url, data=data)
    result = json.loads(json.dumps(r.json()))
    
    
    if result["class"] == "success":
        print "YOUR SHOT IS READY TO UPLOAD!...Proceed further."
        return result
    elif result["message"] == "Invalid API Key":
        nuke.message("Please enter the correct API key.")
    elif result["message"] == "you have no working shots":
        nuke.message("Oops! You are not currently assigned any shot.")
    else:
        nuke.message("Something went wrong. Please try again later.")
    
    r.raw.close()
    
print getInfo(getAPIkey())
 
 
#CREATES PANEL FOR ARTIST
 
def panel(info):
 
    p = nuke.Panel('upload: ' + info['shots']['shot_name'])
    p.addBooleanCheckBox(info['shots']['company_note'], True)
    p.addMultilineTextInput('note to the admin!', '')
    ret = p.show()
    print p.value('note to the admin!')
 
    if p.value(info["shots"]["company_note"]) == False:
        nuke.message("Please confirm you've addressed the note: \n\n" +  info["shots"]["company_note"])
        return False
                        
panel(getInfo(getAPIkey()))
 
 
#GETS INFO ABOUT THE READ NODE SO THAT THE PROGRAM KNOWS WHAT TO UPLOAD
def getReadInfo(x):
    dwaa = exr = bitsPerChannel = False
 
    n = nuke.selectedNode()
    file = n['file'].value().split('/')[-1]
    file = file.split(".")[0]
    first_frame = n["first"].value()
    last_frame = n["last"].value()
    node_name = n["name"].value()
 
    #does not require user to rerender
    # 0 = file // 1 = first_frame // 2 = last_frame // 3 = node_name
    return [file, first_frame, last_frame, node_name]
getReadInfo(getInfo(getAPIkey()))
 
 
#COPIES THE CORRECT READ NODE AND RENDERS USING THAT READ NODE
def renderEXRs(y):
    info = getReadInfo(getInfo(getAPIkey()))
    scratch_dir = scratch
 
    if os.path.exists(scratch_dir + getSep() + info[0] ):
        pass
    else:
        os.mkdir(scratch_dir + getSep() + info[0] )
 
    output_destination = scratch_dir + getSep() + info[0] + getSep() + info[0] + "_%04d.exr"
 
    #EXR WRITER
    nuke.nodePaste(exr_writer)
 
    n = nuke.selectedNode()
    n["file"].setValue(output_destination)
    exr_write_node = n['name'].getValue()
    
    try:
        nuke.execute(exr_write_node, info[1], info[2])
    except:
        print "something went wrong"
 
    #deletes write nodes
    nuke.delete(nuke.toNode(exr_write_node))
 
    #creates zip file
    print scratch_dir + getSep() + info[0]
    zip = zipfile.ZipFile(scratch_dir + getSep() + info[0] + '.zip', mode='w', allowZip64 = True)
    #shutil.make_archive(scratch_dir + getSep() + info[0], 'zip', scratch_dir)
 
    nuke.toNode(info[3]).setSelected(True)
 
    return scratch_dir + getSep() + info[0] + ".zip"
 
 
#UPLOADS
def upload(api):
 
    i = getInfo(api)
    shot_note = panel(i)
    readInfo = getReadInfo(getInfo(getAPIkey()))
    scratch_dir = scratch + "/scratch"
 
    #THIS IS WHERE THE RENDER FUNCTION IS CALLED
    zip_file = renderEXRs(getReadInfo(getInfo(getAPIkey())))
 
    url = "destination url"
 
    data = {"api_key": api, 
                "shot_work_id": i["shots"]["work_id"],
                "artist_note": shot_note
                }
 
    files = {
                'shot_file': open(zip_file, 'rb')
                }
 
    session = requests.Session()
    r = session.post(url, data=data, files=files, stream=True)
 
    print r.json()
    return r.json()
 
    r.raw.close()
 
 
if len(nuke.selectedNodes()) == 1:
    x = upload(getAPIkey())
    if x["success"] == False:
        nuke.message("Submission Failed. Have you already submitted this shot?")
    elif x["success"] == True:
        nuke.message('Submitted to Tarantula')
else:
    nuke.message('please select one read node to upload')
 