# Yerusha Calculator

A Python web application that calculates the *yorshim* (heirs) of a *niftar* according to the laws of *yerusha* (inheritance), and shows step by step how the answer was reached.

## Live site

**https://yerusha-91k3.onrender.com/**

The site is hosted on Render's free plan, so if nobody has visited for a while the first load can take up to a minute while the server wakes up.

## Features

- **Explore:** choose who is alive and who is *niftar* in a family tree, pick whose *yorshim* to find, and see the answer together with a full trace of the reasoning (*ayen alav*, going up to the father, etc.).
- **Demo:** a guided series of cases, each with the relevant explanation (Rashi, Tosafos, the questions of Rami bar Chama, and more). Try to answer each one before the app reveals the solution.
- **Family tree diagram:** an image of the tree is generated for every case, showing who is alive and who is niftar.

## Tech stack

- Python 3 and [Flask](https://flask.palletsprojects.com/)
- [anytree](https://anytree.readthedocs.io/) to model the family tree
- [Graphviz](https://graphviz.org/) to draw the tree images
- [Gunicorn](https://gunicorn.org/) as the production server
- Docker, for deployment on [Render](https://render.com/)

## Run locally

1. Install [Graphviz](https://graphviz.org/download/) so that the `dot` command is available:
   - Ubuntu/Debian: `sudo apt-get install graphviz`
   - macOS: `brew install graphviz`
   - Windows: `winget install Graphviz.Graphviz`
2. Install the Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   python main.py
   ```

4. Open http://localhost:5000 in your browser.

## Run with Docker

```bash
docker build -t yerusha .
docker run -p 10000:10000 yerusha
```

Then open http://localhost:10000.

## Project structure

```
main.py            Flask app and the yerusha logic
templates/         HTML templates
static/css/        Stylesheets
Dockerfile         Container definition (installs Graphviz)
requirements.txt   Python dependencies
```
