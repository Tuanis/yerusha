import glob
import os
import time
import uuid
from types import SimpleNamespace

from flask import (Flask, render_template, request, redirect, url_for,
                   send_file, session, abort)
from anytree import Node
from anytree.exporter import DotExporter

app = Flask(__name__)

# Used to sign the visitor's session cookie. On Render you can set a SECRET_KEY
# environment variable; if you don't, the fallback below is used.
app.secret_key = os.environ.get("SECRET_KEY", "yerusha-change-me")


# ---------------------------------------------------------------------------
# One Calc object per calculation (replaces the old global lists)
# ---------------------------------------------------------------------------
class Calc:
    """Holds the answer and the trace of ONE calculation."""

    def __init__(self):
        self.yorshim = []   # The answer: a list of yorshim
        self.visited = []   # People found not to have live zera
        self.steps = []     # A trace explaining how the answer was found

    def add_yoresh(self, yoresh):
        self.yorshim.append(yoresh)

    def add_step(self, step):
        self.steps.append(step)

    def add_visited(self, person):
        self.visited.append(person)

    def was_visited(self, person):
        return person in self.visited


def be_morish(person):
    calc = Calc()
    calc.add_step(f"\nLooking for the yorshim of {person.name}")
    person.yerusha(calc)
    return calc


class Person:
    """A person in the family tree"""

    def __init__(self, english_name, hebrew_name, father=None, mother=None, is_alive=True):
        self.name = f"{english_name} ({hebrew_name})"
        self.sons = []
        self.daughters = []
        self.father = father  # defaults to None
        self.is_alive = is_alive  # defaults to True

        status = "Alive" if is_alive else "Niftar"
        text = self.name.replace(' ', '\n') + '\n' + status

        if father:
            self.node = Node(text, parent=father.node)
        elif mother:  # I only need this for someone like Chur, so that he shows in trees
            self.node = Node(text, parent=mother.node)
        else:
            self.node = Node(text)

    def set_father(self, father):
        self.father = father

    def add_son(self, son):
        self.sons.append(son)

    def add_sons(self, sons):
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
            text = self.name.replace(' ', '\n') + "\nAlive"
        else:
            text = self.name.replace(' ', '\n') + "\nNiftar"
        self.node.name = text

    def alive(self):
        self.change_living_status(True)

    def dead(self):
        self.change_living_status(False)

    def yerusha(self, calc):
        if self.is_alive:
            calc.add_step(f"{self.name} is alive, and therefore is not morish!")
            calc.add_yoresh(self)
        elif self.ayen_alav(calc):  # Look for yoresh in descendants
            pass  # Found at least one yoresh, so all done
        else:
            if self.father:
                calc.add_step(
                    "Didn't find any live zera, so doing \"mishmush\": going up to father as if he was the niftar")
                self.father.yerusha(calc)
            else:  # Needed in case user asks to see the yorshim of Chur
                calc.add_step(f"{self.name} is not assigned to a father, and therefore is not morish!")
                calc.add_yoresh(self)

    def ayen_alav(self, calc):  # Look for yoresh in descendants
        found_yoresh = False
        calc.add_visited(self)
        if self.has_sons():
            calc.add_step(f"{self.name} is not alive, so doing \"Ayen Alav\": Going down to {self.name}'s sons")
            for son in self.sons:
                calc.add_step(f"Trying with {son.name}")
                if calc.was_visited(son):  # Don't do superfluous work
                    calc.add_step(f"{son.name} was already found not to have live zera")
                else:
                    if son.is_alive:
                        calc.add_yoresh(son)
                        calc.add_step(f"{son.name} is a yoresh!")
                        found_yoresh = True
                    else:
                        calc.add_step(f"{son.name} is not alive")
                        if son.ayen_alav(calc):
                            found_yoresh = True
            calc.add_step(f"End of sons of {self.name}")
        else:
            calc.add_step(f"{self.name} has no sons")
        if not found_yoresh:  # Only if there's no yoresh in sons, then look in daughters
            if self.has_daughters():
                calc.add_step(f"Going down daughters of {self.name}")
                for daughter in self.daughters:
                    calc.add_step(f"Trying with {daughter.name}")
                    if calc.was_visited(daughter):  # Don't do superfluous work
                        calc.add_step(f"{daughter.name} was already found not to have live zera")
                    else:
                        if daughter.is_alive:
                            calc.add_step(f"{daughter.name} is a yoresh!")
                            calc.add_yoresh(daughter)
                            found_yoresh = True
                        else:
                            calc.add_step(f"{daughter.name} is not alive")
                            if daughter.ayen_alav(calc):
                                found_yoresh = True
                calc.add_step(f"End of daughters of {self.name}")
            else:
                calc.add_step(f"{self.name} has no daughters")
        return found_yoresh

    def show_tree(self, path):
        DotExporter(self.node).to_picture(path)


# ---------------------------------------------------------------------------
# The family tree. A fresh copy is built for every request, so visitors
# never affect each other.
# ---------------------------------------------------------------------------
def build_family(dead_names=()):
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
    yaakov.add_sons([reuven, shimon, levi, yehuda, yissachar, zevulun, dan,
                     naftali, gad, asher, yosef, binyamin])
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

    lavan.add_daughters([rachel, leah, bilha, zilpah])
    rachel.add_sons([yosef, binyamin])
    leah.add_sons([reuven, shimon, levi, yehuda, yissachar, zevulun])
    leah.add_daughter(dina)
    bilha.add_sons([dan, naftali])
    zilpah.add_sons([gad, asher])

    # Stam so that it doesn't complain that not defined
    ploni = Person("Ploni", "פלוני")

    # The people shown in the "explore" page (same order as before)
    people = [abraham, yitzchak, yishmael, bakol, yaakov, esav, reuven, shimon, levi,
              yehuda, yissachar, zevulun, dan, naftali, gad, asher, yosef, binyamin,
              dina, chanoch, paluh, chetzron, charmi, kehas, gershon, merari,
              yocheved, serach, menashe, efraim, amram, yitzhar, chevron, uziel,
              miriam, aharon, moshe, chur]

    local_vars = dict(locals())
    fam = SimpleNamespace(**{k: v for k, v in local_vars.items() if isinstance(v, Person)})
    fam.all = [v for v in local_vars.values() if isinstance(v, Person)]
    fam.by_name = {p.name: p for p in fam.all}
    fam.people = people

    for p in fam.all:
        if p.name in dead_names:
            p.dead()
    return fam


# ---------------------------------------------------------------------------
# Per-visitor tree picture
# ---------------------------------------------------------------------------
def tree_path():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return f"/tmp/tree-{session['sid']}.png"


def cleanup_old_trees(max_age_seconds=3600):
    now = time.time()
    for f in glob.glob("/tmp/tree-*.png"):
        try:
            if now - os.path.getmtime(f) > max_age_seconds:
                os.remove(f)
        except OSError:
            pass


def draw_tree(root_person):
    cleanup_old_trees()
    root_person.show_tree(tree_path())


@app.route('/tree.png')
def serve_tree():
    path = tree_path()
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype='image/png')


@app.route('/')
def home():
    return render_template('home.html')


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def A(*names):  # these people are alive
    return [(n, "alive") for n in names]


def D(*names):  # these people are dead
    return [(n, "dead") for n in names]


# Each entry: [message, conditions, whose tree to show, who is the niftar]
# Conditions are cumulative: step N starts from the state left by steps 0..N-1.
demo_steps = [
    ["Daughters don't inherit if there are brothers: When Amram dies, Miriam doesn't get yerusha",
     D("amram") + A("aharon", "moshe", "miriam"),
     "amram",
     "amram"],

    ["Rashi: All descendants of the niftar's sons have priority over the daughters. "
     "For example: Any descendant of Reuven (and Levi and Asher -- even if female) is yoresh before Dina. "
     "We learn from the words 'ein lo' in the pasuk, that we must be 'ayen alav'",
     D("yaakov", "levi", "kehas", "gershon", "merari") + A("yocheved")
     + D("amram", "yitzhar", "chevron", "uziel", "miriam", "aharon", "moshe", "chur", "reuven")
     + A("chanoch", "paluh", "chetzron", "charmi")
     + D("shimon", "yehuda", "yissachar", "zevulun", "dan", "naftali", "gad", "asher",
         "yosef", "binyamin", "menashe", "efraim")
     + A("dina", "serach"),
     "yaakov",
     "yaakov"],

    ["Unless there are only daughters (like benos Tzlofchad), or the sons and their descendants are not alive... "
     "In such a case, a daughter (of the niftar) has priority over [male] brothers (of the niftar). "
     "And even over the father of the niftar",
     D("amram", "aharon", "moshe") + A("miriam", "chur", "kehas", "yitzhar", "chevron", "uziel"),
     "kehas",
     "amram"],

    ["Tosafos: A son's son-or-daughter is not only 'better' than the brothers and father of the niftar, "
     "they are actually equal to the sons of the niftar! "
     "For example, Miriam will even get yerusha from Kehas, together with her father's brothers",
     D("amram", "aharon", "moshe") + A("miriam") + D("kehas") + A("yitzhar", "chevron", "uziel"),
     "kehas",
     "kehas"],

    ["And even her offspring... (Chur is the son of Miriam and Kalev)",
     D("amram", "aharon", "moshe", "miriam") + A("chur") + D("kehas") + A("yitzhar", "chevron", "uziel"),
     "kehas",
     "kehas"],

    ["Brothers don't get yerusha, if the father is alive",
     A("kehas", "amram") + D("yitzhar") + A("chevron", "uziel"),
     "kehas",
     "yitzhar"],

    ["But brothers have priority over the father's brothers (=uncles)",
     D("kehas") + A("yitzhar", "chevron", "uziel") + D("amram") + A("aharon") + D("moshe") + A("miriam"),
     "kehas",
     "moshe"],

    ["Rashi: Even a sister has priority over the father's brothers (=uncles), "
     "and even over the father's father (=grandfather)",
     A("kehas", "yitzhar", "chevron", "uziel") + D("amram", "aharon", "moshe") + A("miriam"),
     "kehas",
     "moshe"],

    ["Rashi: Anyone who has priority in yerusha, and is himself dead, his descendants have priority "
     "even over closer relatives of the niftar. "
     "For example, a great-grandson is yoresh before a brother or a father",
     A("yaakov") + D("levi", "kehas", "gershon", "merari", "yocheved")
     + D("amram", "yitzhar", "chevron", "uziel", "miriam", "aharon", "moshe") + A("chur")
     + A("reuven", "shimon", "yehuda", "yissachar", "zevulun", "dan", "naftali", "gad",
         "asher", "yosef", "binyamin"),
     "yaakov",
     "levi"],

    ["If a niftar has 2 daughters, and one of them is already dead herself, and she has a son, "
     "the live daughter certainly gets yerusha together with her nephew (even though he is male) "
     "because he's getting yerusha in place of his mother",
     D("lavan", "rachel") + A("yosef", "binyamin", "leah", "bilha", "zilpah"),
     "lavan",
     "lavan"],

    ["We don't say (as the Tzdukim said) that \"a daughter inherits together with a son's daughter\" "
     "For example, Dina will not inherit Yaakov together with Serach bas Asher and Yocheved",
     D("yaakov", "levi", "kehas", "gershon", "merari") + A("yocheved")
     + D("amram", "yitzhar", "chevron", "uziel", "miriam", "aharon", "moshe", "chur",
         "reuven", "chanoch", "paluh", "chetzron", "charmi", "shimon", "yehuda", "yissachar",
         "zevulun", "dan", "naftali", "gad", "asher", "yosef", "binyamin")
     + A("dina", "serach") + D("menashe", "efraim"),
     "yaakov",
     "yaakov"],

    # It will report that Yocheved has no sons&daughters, because they're assigned to Amram...
    ["A great grandfather can be a yoresh of a great grandson!",
     A("abraham") + D("yitzchak", "esav", "yaakov", "levi", "kehas", "gershon", "merari", "yocheved",
                      "amram", "yitzhar", "chevron", "uziel", "miriam", "aharon", "moshe", "chur",
                      "reuven", "shimon", "yehuda", "yissachar", "zevulun", "dan", "naftali", "gad",
                      "asher", "yosef", "binyamin", "menashe", "efraim", "dina", "serach"),
     "abraham",
     "amram"],

    ["Rami bar Chama's first question [116a]: Who inherits Esav, Abraham or Yishamel? "
     "For sure a grandfather is before an uncle!",
     A("abraham", "yishmael") + D("yitzchak", "esav", "yaakov"),
     "abraham",
     "esav"],

    ["Rami bar Chama's second question [116a]: Who inherits Esav, Abraham or Yaakov? "
     "A nephew comes before a grandfather!",
     A("abraham") + D("yishmael", "yitzchak", "esav") + A("yaakov"),
     "abraham",
     "esav"],
]


def family_for_demo(index):
    """Build the family and apply demo steps 0..index cumulatively."""
    fam = build_family()
    for i in range(index + 1):
        for key, state in demo_steps[i][1]:
            person = getattr(fam, key)
            if state == "alive":
                person.alive()
            else:
                person.dead()
    return fam


@app.route('/demo')
def demo():
    return redirect(url_for('step_by_step', step=0))


@app.route('/demo/<int:step>', methods=["GET", "POST"])
def step_by_step(step):
    # min() prevents a user from typing "/demo/20" (for example) in the URL
    index = min(step, len(demo_steps) - 1)

    message, _conditions, root_key, niftar_key = demo_steps[index]
    fam = family_for_demo(index)
    niftar = getattr(fam, niftar_key)

    draw_tree(getattr(fam, root_key))
    calc = be_morish(niftar)

    if request.method == "POST":
        if 'yes' in request.form:
            return render_template('demo.html',
                                   message=message,
                                   name=niftar.name,
                                   yorshim=calc.yorshim,
                                   trace=calc.steps,
                                   show_answer=True)
        next_index = index + 1
        if next_index < len(demo_steps):
            return redirect(url_for('step_by_step', step=next_index))
        return redirect(url_for('finished'))

    return render_template('demo.html',
                           message=message,
                           name=niftar.name,
                           yorshim=calc.yorshim,
                           show_answer=False)


@app.route('/finished')
def finished():
    return render_template('finished.html')


# ---------------------------------------------------------------------------
# Explore
# ---------------------------------------------------------------------------
@app.route('/explore', methods=["GET", "POST"])
def explore():
    dead_names = set(session.get("dead", []))
    fam = build_family(dead_names)
    people = fam.people
    niftar = fam.by_name.get(session.get("niftar"), fam.ploni)

    if request.method == "POST":
        req = request.form

        if 'yes' in req:
            draw_tree(fam.abraham)
            calc = be_morish(niftar)
            return render_template('explore.html',
                                   people=people,
                                   name=niftar.name,
                                   yorshim=calc.yorshim,
                                   trace=calc.steps,
                                   show_yorshim=True,
                                   show_answer=True)

        if 'go' in req:
            morish = req.get('morish')
            for person in people:
                # If user changed living status, take care of it
                wanted = req.get(f"is {person.name} alive")
                if wanted == "dead":
                    person.dead()
                elif wanted == "alive":
                    person.alive()
                # Need to go from name (text) to person (object)
                if person.name == morish:
                    niftar = person
            session["dead"] = [p.name for p in fam.all if not p.is_alive]
            session["niftar"] = niftar.name

        calc = be_morish(niftar)
        draw_tree(fam.abraham)
        return render_template('explore.html',
                               people=people,
                               name=niftar.name,
                               yorshim=calc.yorshim,
                               show_yorshim=True,
                               show_answer=False)

    draw_tree(fam.abraham)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
