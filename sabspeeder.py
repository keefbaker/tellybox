#!/usr/bin/env python
import web
import httplib
import json
import os
import pickle
from web import form
#
# api keys and urls
sick_apikey = "de28d01cd176dfd278a39faa75b5462d"
sab_apikey = "f8d4fcf8bc5337ede6a4945065b44258"
sab_url = "192.168.1.100:8800"
sick_url = "192.168.1.100:7071"
#
# form build
#
drop_list = []
tv_list = []
old_message = " "
screen_message = " "
my_form = form.Form(
 form.Button("btn", id="Extreme", value="10", html="Extreme Limiting", class_="10"),
 form.Button("btn", id="Daytime", value="100", html="Daytime Limiting", class_="100"),
 form.Button("btn", id="None", value="0", html="No Limit", class_="0")
)
form_two = form.Form(
 form.Dropdown("seasons", drop_list),
 form.Button("grab", id="None", value="go", html="Grab Missing Episodes", class_="go")
)
form_three = form.Form(
 form.Dropdown("shows", tv_list),
 form.Button("grablast", id="None", value="go", html="Grab from latest season", class_="go")
)

form_four = form.Form(
 form.Button("repo", id="None", value="go", html="Repopulate season information", class_="go")
 )
#
# break out of nested loop
class BreakOut(Exception): pass
#
# grab current speed setting
#
def grabSickShows():
    pkl_file = open('showdb.pkl', 'wb')
    showdict = {}
    try:
        connsa = httplib.HTTPConnection(sick_url)
        connsa.request("GET","/api/1234/?cmd=shows&apikey="+sick_apikey)
        jsonsick= connsa.getresponse().read()
        showlist = json.loads(jsonsick)["data"]
        showdict = {}
        for show in showlist:
            sname = json.loads(jsonsick)["data"][show]["show_name"]
            connsb = httplib.HTTPConnection(sick_url)
            connsb.request("GET","/api/1234/?cmd=show.seasonlist&tvdbid="+show+"&apikey="+sick_apikey)
            jsonsick2 = connsb.getresponse().read()
            showdict[show] = {}
            showdict[show][sname] = []
            showdict[show][sname] = json.loads(jsonsick2)["data"]
        pickle.dump(showdict, output)
    except:
        showdict["noID"] = {}
        showdict["noID"]["noShit"] = [ "noSeason99" ]
        pickle.dump(showdict, pkl_file)
        pkl_file.close()
    global screen_message 
    screen_message = "I've refilled stuff like you asked"
def grabSettings():
    try:
        conn = httplib.HTTPConnection(sab_url)
        conn.request("GET","/api?mode=queue&start=START&limit=LIMIT&output=json&apikey="+sab_apikey)
        jsonout= conn.getresponse().read()
        try:
            current_setting = int(json.loads(jsonout)["queue"]["speedlimit"])
        except:
            current_setting = 9999
        queue_size = json.loads(jsonout)["queue"]["sizeleft"]
    except:
        current_setting = 9999
        queue_size = "no info"

    if current_setting == 9999:
        message = "ALBERT IS IN YOUR INTERNETS! NOTHING WILL WORK!!"
        pic = "albert.jpg"
    elif current_setting == 10:
        message = "Extreme limiting"
        pic = "sleeps.jpg"
    elif current_setting == 100:
        message = "Daytime Limiting"
        pic = "binky.jpg"
    elif current_setting == 0:
        message = "No Limiting"
    else:
        message = "It's set to %rk, I runno what's going on" % current_setting
		pic = "noidea.jpg"
    return message, pic, queue_size
#
# Set the limited speed from the webform postdata
#
def grabMissingEpisodes(season):
    choppedData = season.split("~")
    with open('showdb.pkl', 'rb') as show_db:
        showdict = pickle.load(show_db)
    if choppedData[1] == "Season":
        num = 2
    else:
        for i in choppedData:
            if i == "Season":
                choppedData[0]= "~".join(choppedData[0:i])
                num = i + 1
    try:
        for k in showdict:
            for v in showdict[k]:
                if choppedData[0] == v:
                    tvdbid = k
                    if choppedData[num] == "x":
                        showdict[k][v].sort()
                        choppedData[num] = showdict[k][v][-1]
                    raise BreakOut
    except:
        pass
    try:
        conkt = httplib.HTTPConnection(sick_url)
        conkt.request("GET","/api/1234/?cmd=show.seasons&tvdbid="+str(tvdbid)+"&season="+str(choppedData[num])+"&apikey="+sick_apikey)
    except:
        print "balls!"
    jsonick= conkt.getresponse().read()
    seasondata = json.loads(jsonick)["data"]
    epcount = 0
    grabs = 0
    for episode in seasondata:
        epcount +=1
        if seasondata[episode]["status"] == "Snatched":
            grabs +=1
    conkr = httplib.HTTPConnection(sick_url)
    conkr.request("GET","/api/1234/?cmd=episode.setstatus&tvdbid="+str(tvdbid)+"&season="+str(choppedData[num])+"&status=wanted&apikey="+sick_apikey)
    jsonrck= conkr.getresponse().read()
    global screen_message
    screen_message = "%s season %s has %d out of %d missing. now set to wanted" % (choppedData[0], choppedData[num], grabs, epcount)
    
#
# Sets the speed limit in sabnzb
#
def setSpeed(speedlimit):
    try:
        conn2 = httplib.HTTPConnection(sab_url)
        conn2.request("GET","/api?mode=config&name=speedlimit&value="+speedlimit+"&apikey="+sab_apikey)
    except:
        pass
    global screen_message
    screen_message = "Set like you asked"
#
# Kick off web.py
#
render = web.template.render('templates/')

urls = ('/', 'index', '/images/(.*)', 'images')
app = web.application(urls, globals())
#
# fun web stuff here, lol
#
class images:
    def GET(self,name):
        ext = name.split(".")[-1]

        cType = {
            "png":"images/png",
            "jpg":"images/jpeg",
            "gif":"images/gif",
            "ico":"images/x-icon"            }

        if name in os.listdir('images'): 
            web.header("Content-Type", cType[ext]) 
            return open('images/%s'%name,"rb").read() 
        else:
            raise web.notfound()
class index: 
    def GET(self):
        speed_setting, picture, qsize = grabSettings()
        showdict = {}
        if os.path.isfile('showdb.pkl') and int(os.path.getsize('showdb.pkl')) > 0:
            with open('showdb.pkl', 'rb') as show_db:
                showdict = pickle.load(show_db)
        else:
            grabSickShows()
            showdict = {}
            showdict["database"] = {}
            showdict["database"]["building"] = ["database"]
        
        for tvid in showdict:
            for tvshow in showdict[tvid]:
                if tvshow not in tv_list:
                    tv_list.append(tvshow)
                    for tvseason in showdict[tvid][tvshow]:
                        if tvseason != 0:
                            if "%s~Season~%s" % (tvshow, tvseason) not in drop_list:
                                drop_list.append("%s~Season~%s" % (tvshow, tvseason))
        drop_list.sort()
        tv_list.sort()
	global old_message
	global screen_message
        if old_message == screen_message:
            screen_message = " "
        old_message = screen_message
        web_form = my_form()
        web_form2 = form_two()
        web_form3 = form_three()
        web_form4 = form_four()
        return render.index(web_form, speed_setting, picture, qsize, web_form2, web_form3, web_form4, screen_message)
    def POST(self):
        web_form = my_form()
        userData = web.input()
        if not web_form.validates(): 
            return render.formtest(web_form)
        else:
            try:
                setSpeed(userData.btn)
            except:
                pass
            try:
                if userData.grab == "go":
                    grabMissingEpisodes(userData.seasons)
            except:
                pass
            try:
                if userData.grablast == "go":
                    grabMissingEpisodes(userData.shows+"~Season~x")
            except:
                pass

            try:
                if userData.repo == "go":
                    grabSickShows()
            except:
                pass
        raise web.seeother('/')

#
# kick off the site 
#
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
