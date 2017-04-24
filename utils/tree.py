import json
datafile = open('../json/activities.json', 'r')
acts = json.loads(datafile.read().decode("utf-8"))
datafile = open('../json/screens.json', 'r')
screens = json.loads(datafile.read().decode("utf-8"))

exitCriteria = {'','other specify','other people','home','enjoyment'}

def recursive(node,level):
    level += 1
    for branch in screens['screens'][node]['activities']:
            nextNode = acts['activities'][branch]['next']
            caption  = acts['activities'][branch]['caption']
            id       = acts['activities'][branch]['ID']
            title    = acts['activities'][branch]['title']
            icon     = 'NONE'
            try:
                icon = acts['activities'][branch]['icon']
            except:
                pass

            print "{:<25}{:<35}{:>6} {:<15}{:<35}".format('.  '*level + caption, title, id, icon, branch)
            if not (nextNode in exitCriteria):
                try:
                    recursive(nextNode,level)
                except KeyError:
                    print 'ERROR at: ' + node + ' > ' + branch + ' > ' + nextNode

recursive('activity main',-1)
# recursive('activity root',-1)
    
