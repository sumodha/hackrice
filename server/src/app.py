# Import the Flask class from the flask library
from flask import Flask

# Create an instance of the Flask class.
# __name__ is a special Python variable that gets the name of the current module.
# Flask uses this to know where to look for resources like templates and static files.
app = Flask(__name__)

# Use the route() decorator to tell Flask what URL should trigger our function.
# In this case, the '/' URL is the root of our website.
@app.route('/')
def hello_world():
    """This function will run when someone visits the root URL."""
    return 'Hello, World!'

# This is the standard entry point for a Python script.
# The code inside this block will only run when the script is executed directly.
if __name__ == '__main__':
    # The app.run() method starts the Flask development server.
    # debug=True will automatically reload the server when you make code changes
    # and show detailed error pages if something goes wrong.
    app.run(debug=True)

