from flask import Flask, render_template, request, redirect, url_for
from anytree import Node
from anytree.exporter import DotExporter

app = Flask(__name__)


yorshim = []  # This will contain the answer: a list of yorshim.
visited = []
steps = []  # A trace explaining how the answer was found


def clear_all():
    global yorshim
    global visited
    global steps
    yorshim.clear()
    visited.clear()
    steps.clear()


def add_yoresh(yoresh):
    yorshim.append(yoresh)


def add_step(step):
    steps.append(step)


def add_visited(person):  # Person was found not to have live zera
    visited.append(person)


def was_visited(person):
    return person in visited


def be_morish(person):
    clear_all()
    add_step(f"\nLooking for the yorshim of {person.name}")
    person.yerusha()


class Person:
    """A person in the family tree"""

    def __init__(self, english_name, hebrew_name, father=None, mother=None, is_alive=True):
        self.name = f"{english_name} ({hebrew_name})"
        self.sons = []
        self.daughters = []
        self.father = father  # defaults to None
        self.is_alive = is_alive  # defaults to True
        if is_alive:
            status = "Alive"
        else:
            status = "Niftar"
        text = self.name.replace(' ','\n') + '\n' + status
        if father:
            self.node = Node(text, parent=father.node)
        elif mother:  # I only need this for someone like Chur, so that he shows in trees
            self.node = Node(text, parent=mother.node)
        else:
            self.node = Node(text)


    # I don't really use the following, really here for completeness
    # Can also be used to disconnect a person (and his offsprings) from the tree, by setting father to None
    def set_father(self, father):
        self.father = father

    def add_son(self, son):  # Add a single person as a son
        self.sons.append(son)

    def add_sons(self, sons):  # Add a list of sons
        self.sons += sons

    def has_sons(self):
        return self.sons != []

    def add_daughter(self, daughter):
        self.daughters.append(daughter)

    def add_daughters(self, daughters):
        self.daughters += daughters

    def has_daughters(self):
        return self.daughters != []

    def change_living_status(self, status):
        self.is_alive = status
        if status:
            text = self.name.replace(' ','\n') + "\nAlive"
        else:
            text = self.name.replace(' ','\n') + "\nNiftar"
        self.node.name = text

    def alive(self):
        self.change_living_status(True)

    def dead(self):
        self.change_living_status(False)

    def yerusha(self):
        if self.is_alive:
            add_step(f"{self.name} is alive, and therefore is not morish!")
            add_yoresh(self)
        elif self.ayen_alav():  # Look for yoresh in descendants
            pass  # Found at least one yoresh, so all done
        else:
            if self.father:
                add_step(
                    "Didn't find any live zera, so doing \"mishmush\": going up to father as if he was the niftar")
                self.father.yerusha()
            else:  # Needed in case user asks to see the yorshim of Chur
                add_step(f"{self.name} is not assigned to a father, and therefore is not morish!")
                add_yoresh(self)

    def ayen_alav(self):  # Look for yoresh in descendants
        found_yoresh = False
        add_visited(self)
        if self.has_sons():
            add_step(f"{self.name} is not alive, so doing \"Ayen Alav\": Going down to {self.name}'s sons")
            for son in self.sons:
                add_step(f"Trying with {son.name}")
                if was_visited(son):  # Don't do superfluous work
                    add_step(f"{son.name} was already found not to have live zera")
                else:
                    if son.is_alive:
                        add_yoresh(son)
                        add_step(f"{son.name} is a yoresh!")
                        found_yoresh = True
                    else:
                        add_step(f"{son.name} is not alive")
                        if son.ayen_alav():
                            found_yoresh = True
            add_step(f"End of sons of {self.name}")
        else:
            add_step(f"{self.name} has no sons")
        if not found_yoresh:  # Only if there's no yoresh in sons, then look in daughters
            if self.has_daughters():
                add_step(f"Going down daughters of {self.name}")
                for daughter in self.daughters:
                    add_step(f"Trying with {daughter.name}")
                    if was_visited(daughter):  # Don't do superfluous work
                        add_step(f"{daughter.name} was already found not to have live zera")
                    else:
                        if daughter.is_alive:
                            add_step(f"{daughter.name} is a yoresh!")
                            add_yoresh(daughter)
                            found_yoresh = True
                        else:
                            add_step(f"{daughter.name} is not alive")
                            if daughter.ayen_alav():
                                found_yoresh = True
                add_step(f"End of daughters of {self.name}")
            else:
                add_step(f"{self.name} has no daughters")
        return found_yoresh

    def show_tree(self):
       DotExporter(self.node).to_picture("/tmp/tree.png")

from flask import send_file

@app.route('/tree.png')
def serve_tree():
    return send_file("/tmp/tree.png", mimetype='image/png')

# The Family Tree
abraham = Person("Abraham", "אברהם")
yitzchak = Person("Yitzchak", "יצחק", father=abraham)
yishmael = Person("Yishmael", "ישמעאל", father=abraham)
yaakov = Person("Yaakov", "יעקב", father=yitzchak)
esav = Person("Esav", "עשיו", father=yitzchak)
reuven = Person("Reuven", "ראובן", father=yaakov)
chanoch = Person("Chanoch", "חנוך", father=reuven)
paluh = Person("Paluh", "פלוא", father=reuven)
chetzron = Person("Chetzron", "חצרון", father=reuven)
charmi = Person("Charmi", "כרמי", father=reuven)
shimon = Person("Shimon", "שמעון", father=yaakov)
levi = Person("Levi", "לוי", father=yaakov)
yehuda = Person("Yehuda", "יהודה", father=yaakov)
yissachar = Person("Yissachar", "יששכר", father=yaakov)
zevulun = Person("Zevulun", "זבולון", father=yaakov)
dan = Person("Dan", "דן", father=yaakov)
naftali = Person("Naftali", "נפתלי", father=yaakov)
gad = Person("Gad", "גד", father=yaakov)
asher = Person("Asher", "אשר", father=yaakov)
yosef = Person("Yosef", "יוסף", father=yaakov)
binyamin = Person("Binyamin", "בנימין", father=yaakov)
menashe = Person("Menashe", "מנשה", father=yosef)
efraim = Person("Efraim", "אפרים", father=yosef)
dina = Person("Dina", "דינה", father=yaakov)
kehas = Person("Kehas", "קהת", father=levi)
gershon = Person("Gershon", "גרשון", father=levi)
merari = Person("Merari", "מררי", father=levi)
yocheved = Person("Yocheved", "יוכבד", father=levi)
amram = Person("Amram", "עמרם", father=kehas)
yitzhar = Person("Yitzhar", "יצהר", father=kehas)
chevron = Person("Chevron", "חברון", father=kehas)
uziel = Person("Uziel", "עוזיאל", father=kehas)
miriam = Person("Miriam", "מרים", father=amram)
aharon = Person("Aharon", "אהרן", father=amram)
moshe = Person("Moshe", "משה", father=amram)
chur = Person("Chur", "חור", mother=miriam)  # Not connected to a father

bakol = Person("Bakol", "בכל", father=abraham)
serach = Person("Serach", "סרח", father=asher)

abraham.add_sons([yishmael, yitzchak])
abraham.add_daughter(bakol)
yitzchak.add_sons([esav, yaakov])
yaakov.add_sons([reuven, shimon, levi, yehuda, yissachar, zevulun, dan, naftali, gad, asher, yosef, binyamin])
yaakov.add_daughter(dina)
yosef.add_sons([menashe, efraim])
reuven.add_sons([chanoch, paluh, chetzron, charmi])
levi.add_sons([kehas, gershon, merari])
levi.add_daughter(yocheved)
asher.add_daughter(serach)
kehas.add_sons([amram, yitzhar, chevron, uziel])
amram.add_sons([aharon, moshe])
amram.add_daughter(miriam)
miriam.add_son(chur)

# A separate tree
lavan = Person("Lavan", "לבן")
rachel = Person("Rachel", "רחל", father=lavan)
leah = Person("Leah", "לאה", father=lavan)
bilha = Person("Bilha", "בלהה", father=lavan)
zilpah = Person("Zilpah", "זלפה", father=lavan)
lavan.add_daughters([rachel,leah,bilha,zilpah])
rachel.add_sons([yosef,binyamin])
leah.add_sons([reuven,shimon,levi,yehuda,yissachar,zevulun])
leah.add_daughter(dina)
bilha.add_sons([dan,naftali])
zilpah.add_sons([gad,asher])

@app.route('/')
def home():
    return render_template('home.html')

index :int
demo_steps = [  # Maybe this should be in a database!
    ["Daughters don't inherit if there are brothers: When Amram dies, Miriam doesn't get yerusha",  # message
     [(amram,"dead"),(aharon,"alive"),(moshe,"alive"),(miriam,"alive")],  # conditions
     amram,  # who's tree to show
     amram],  # who to be morish
    ["Rashi: All descendants of the niftar's sons have priority over the daughters. \
    For example: Any descendant of Reuven (and Levi and Asher -- even if female) is yoresh before Dina. \
    We learn from the words 'ein lo' in the pasuk, that we must be 'ayen alav'",
     [(yaakov,"dead"),
      (levi,"dead"),(kehas,"dead"),(gershon,"dead"),(merari,"dead"),(yocheved,"alive"),
      (amram,"dead"),(yitzhar,"dead"),(chevron,"dead"),(uziel,"dead"),
      (miriam,"dead"),(aharon,"dead"),(moshe,"dead"),(chur,"dead"),
      (reuven,"dead"),(chanoch,"alive"),(paluh,"alive"),(chetzron,"alive"),(charmi,"alive"),
      (shimon,"dead"),(yehuda,"dead"),(yissachar,"dead"),(zevulun,"dead"),
      (dan,"dead"),(naftali,"dead"),(gad,"dead"),(asher,"dead"),(yosef,"dead"),(binyamin,"dead"),
      (menashe,"dead"),(efraim,"dead"),(dina,"alive"),(serach,"alive")],
     yaakov,
     yaakov],
    ["Unless there are only daughters (like benos Tzlofchad), or the sons and their descendants are not alive... \
    In such a case, a daughter (of the niftar) has priority over [male] brothers (of the niftar). \
    And even over the father of the niftar",
     [(amram,"dead"),(aharon,"dead"),(moshe,"dead"),(miriam,"alive"),(chur,"alive"),
      (kehas,"alive"),(yitzhar,"alive"),(chevron,"alive"),(uziel,"alive")],
     kehas,
     amram],
    ["Tosafos: A son's son-or-daughter is not only 'better' than the brothers and father of the niftar, \
    they are actually equal to the sons of the niftar! \
    For example, Miriam will even get yerusha from Kehas, together with her father's brothers",
     [(amram,"dead"),(aharon,"dead"),(moshe,"dead"),(miriam,"alive"),
      (kehas,"dead"),(yitzhar,"alive"),(chevron,"alive"),(uziel,"alive")],
     kehas,
     kehas],
    ["And even her offspring... (Chur is the son of Miriam and Kalev)",
     [(amram,"dead"),(aharon,"dead"),(moshe,"dead"),(miriam,"dead"),(chur,"alive"),
      (kehas,"dead"),(yitzhar,"alive"),(chevron,"alive"),(uziel,"alive")],
     kehas,
     kehas],
    ["Brothers don't get yerusha, if the father is alive",
     [(kehas,"alive"),(amram,"alive"),(yitzhar,"dead"),(chevron,"alive"),(uziel,"alive")],
     kehas,
     yitzhar],
    ["But brothers have priority over the father's brothers (=uncles)",
     [(kehas,"dead"),(yitzhar,"alive"),(chevron,"alive"),(uziel,"alive"),
      (amram,"dead"),(aharon,"alive"),(moshe,"dead"),(miriam,"alive")],
     kehas,
     moshe],
    ["Rashi: Even a sister has priority over the father's brothers (=uncles), \
    and even over the father's father (=grandfather)",
     [(kehas,"alive"),(yitzhar,"alive"),(chevron,"alive"),(uziel,"alive"),
      (amram,"dead"),(aharon,"dead"),(moshe,"dead"),(miriam,"alive")],
     kehas,
     moshe],
    ["Rashi: Anyone who has priority in yerusha, and is himself dead, his descendants have priority \
    even over closer relatives of the niftar. \
    For example, a great-grandson is yoresh before a brother or a father",
     [(yaakov,"alive"),
      (levi,"dead"),(kehas,"dead"),(gershon,"dead"),(merari,"dead"),(yocheved,"dead"),
      (amram,"dead"),(yitzhar,"dead"),(chevron,"dead"),(uziel,"dead"),
      (miriam,"dead"),(aharon,"dead"),(moshe,"dead"),(chur,"alive"),
      (reuven,"alive"),(shimon,"alive"),(yehuda,"alive"),(yissachar,"alive"),(zevulun,"alive"),
      (dan,"alive"),(naftali,"alive"),(gad,"alive"),(asher,"alive"),(yosef,"alive"),(binyamin,"alive")],
     yaakov,
     levi],
    ["If a niftar has 2 daughters, and one of them is already dead herself, and she has a son, \
    the live daughter certainly gets yerusha together with her nephew (even though he is male) \
    because he's getting yerusha in place of his mother",
     [(lavan,"dead"),(rachel,"dead"),(yosef,"alive"),(binyamin,"alive"),
      (leah,"alive"),(bilha,"alive"),(zilpah,"alive")],
     lavan,
     lavan],
    ["We don't say (as the Tzdukim said) that \"a daughter inherits together with a son's daughter\" \
    For example, Dina will not inherit Yaakov together with Serach bas Asher and Yocheved",
     [(yaakov,"dead"),
      (levi,"dead"),(kehas,"dead"),(gershon,"dead"),(merari,"dead"),(yocheved,"alive"),
      (amram,"dead"),(yitzhar,"dead"),(chevron,"dead"),(uziel,"dead"),
      (miriam,"dead"),(aharon,"dead"),(moshe,"dead"),(chur,"dead"),
      (reuven,"dead"),(chanoch,"dead"),(paluh,"dead"),(chetzron,"dead"),(charmi,"dead"),
      (shimon,"dead"),(yehuda,"dead"),(yissachar,"dead"),(zevulun,"dead"),
      (dan,"dead"),(naftali,"dead"),(gad,"dead"),(asher,"dead"),(yosef,"dead"),(binyamin,"dead"),
      (dina,"alive"),(serach,"alive"),(menashe,"dead"),(efraim,"dead")],
     yaakov,
     yaakov],
    ["A great grandfather can be a yoresh of a great grandson!",
     # It will report that Yocheved has no sons&daughters, because they're assigned to Amram...
     [(abraham,"alive"),(yitzchak,"dead"),
      (esav,"dead"),(yaakov,"dead"),
      (levi,"dead"),(kehas,"dead"),(gershon,"dead"),(merari,"dead"),(yocheved,"dead"),
      (amram,"dead"),(yitzhar,"dead"),(chevron,"dead"),(uziel,"dead"),
      (miriam,"dead"),(aharon,"dead"),(moshe,"dead"),(chur,"dead"),
      (reuven,"dead"),(shimon,"dead"),(yehuda,"dead"),(yissachar,"dead"),(zevulun,"dead"),
      (dan,"dead"),(naftali,"dead"),(gad,"dead"),(asher,"dead"),(yosef,"dead"),(binyamin,"dead"),
      (menashe,"dead"),(efraim,"dead"),
      (dina,"dead"),(serach,"dead")],
     abraham,
     amram],
    ["Rami bar Chama's first question [116a]: Who inherits Esav, Abraham or Yishamel? \
    For sure a grandfather is before an uncle!",
     [(abraham,"alive"),(yishmael,"alive"),(yitzchak,"dead"),(esav,"dead"),(yaakov,"dead")],
     abraham,
     esav],
    ["Rami bar Chama's second question [116a]: Who inherits Esav, Abraham or Yaakov? \
    A nephew comes before a grandfather!",
     [(abraham,"alive"),(yishmael,"dead"),(yitzchak,"dead"),(esav,"dead"),(yaakov,"alive")],
     abraham,
     esav]
    ]

# demo just calls step_by_step(), but it always starts from 0
@app.route('/demo')
def demo():
    global index
    index = 0
    return redirect(url_for('step_by_step', step=index))
    step_by_step(index)

@app.route('/demo/<int:step>', methods = ["GET", "POST"])
def step_by_step(step):
    global index, demo_steps, yorshim, steps
    index = min(step, len(demo_steps)-1)  # to prevent a user from typing "/demo/20" (for example) in the URL
    message = demo_steps[index][0]
    conditions = demo_steps[index][1]
    root = demo_steps[index][2]
    niftar = demo_steps[index][3]
    for condition in conditions:
        person = condition[0]
        matzav = condition[1]
        if matzav == "alive":
            person.alive()
        elif matzav == "dead":
            person.dead()
    root.show_tree()
    be_morish(niftar)
    if request.method == "POST":
        if 'yes' in request.form:
            return render_template('demo.html',
                                   message = message,
                                   name = niftar.name,
                                   yorshim = yorshim,
                                   trace = steps,
                                   show_answer = True)
        elif 'no' or 'next' in request.form:
            index += 1
            if index < len(demo_steps):
                return redirect(url_for('step_by_step', step=index))
                step_by_step(index)
            else:
                return redirect(url_for('finished'))
    elif request.method == "GET":
        return render_template('demo.html',
                   message = message,
                   name = niftar.name,
                   yorshim = yorshim,
                   show_answer = False)

@app.route('/finished')
def finished():
    return render_template('finished.html')

# It is possible to get all names from anytree, but I need objects, not names...
people = [abraham,yitzchak,yishmael,bakol,yaakov,esav,reuven,shimon,levi,yehuda,yissachar,zevulun,dan,naftali,gad,asher,yosef,binyamin,dina,chanoch,paluh,chetzron,charmi,kehas,gershon,merari,yocheved,serach,menashe,efraim,amram,yitzhar,chevron,uziel,miriam,aharon,moshe,chur]

niftar = Person("Ploni", "פלוני") # Stam so that it doesn't complain that not defined
@app.route('/explore', methods = ["GET", "POST"])
def explore():
    abraham.show_tree()
    global people, yorshim, steps, niftar
    if request.method == "POST":
        req = request.form
        morish = req.get('morish')
        if 'yes' in req:
            return render_template('explore.html',
                                   people=people,
                                   name=niftar.name,
                                   yorshim=yorshim,
                                   trace=steps,
                                   show_yorshim=True,
                                   show_answer=True)
        elif 'no' or 'go' in req:
            if 'go' in req:
                for person in people:
                    # If user changed living status, take care of it
                    if person.is_alive and req[f"is {person.name} alive"] == "dead":
                        person.dead()
                    elif not(person.is_alive) and req[f"is {person.name} alive"] == "alive":
                        person.alive()
                    # Need to go from name (text) to person (object)
                    if person.name == morish:  # there seems not to be a nicer way of doing this
                        niftar = person
                be_morish(niftar)
                abraham.show_tree()
            return render_template('explore.html',
                                   people=people,
                                   name=niftar.name,
                                   yorshim=yorshim,
                                   show_yorshim=True,
                                   show_answer=False)
    elif request.method == "GET":
        return render_template('explore.html',
                               people=people,
                               name=niftar.name,
                               show_yorshim=False,
                               show_answer=False)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# This prevents user from writing whatever he wants at the URL
@app.route('/<path:u_path>')
def catch_all(u_path):
    return render_template('home.html')

# The following prevents the images in demos from being cached
@app.after_request
def add_header(response):
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response
