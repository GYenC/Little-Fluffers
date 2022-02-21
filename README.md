# LITTLE FLUFFERS
#### Video Demo: https://youtu.be/8cnEMsjNcZ4
#### The idea:
Little Fluffers was designed to share basic petcare information in the event of absence or emergency. The idea stemmed from keeping exotic pets, where a sitter or next of kin may not know what to do. Little Fluffers is not just for the unusual pets though! It can also be a useful tool if you have multiple pets, ones with dietary needs, ones on long-term medication, etc. All of the information is stored and can be accessed by a guest at any time.

Little Fluffers is a website built on a Flask framework, with a PostgreSQL database.

Thanks to Zongyi Chen for providing the photo for 'Dino' featured in the video demo.

#### How it works:
The premise is that a user can register and add pets to their profile, and will keep each entry updated. Each user has a unique guest pass, which they can share with anyone at any time - this way, a guest will have their pass to hand in the case of an emergency. This pass grants access to the essential and current information, so that they can provide adequate temporary care to any animal.

#### The pages:
There are a total of 12 HTML files, including 1 layout files. This could feasibly have been cut down to fewer pages (addpet/editpet/viewpet could arguably be combined in some way) but I feel have each section laid out simply was a better choice overall. There is a fair amount of information per entry and keeping it a simple as possible lends to the overall user experience.

One might notice that the date of death and handling of deceased pets is conspicuously missing. This needs to be handled sensitively, and any future implementation must take user feedback into account. Depending on the individual, there may be a preference for deletion, archiving, or just leaving the entries as active.

#### The client actions:
Through app.py, any images uploaded by the user is saved to static/imgs. There is only 1 file allowed per pet entry, and it is overwritten with subsequent uploads. This was a feature that lends itself to the idea of Little Fluffers but comes with its own risks. To mitigate these, the allowed file types was limited, and the file names are put through checks. The renaming to random string was done so that each image will have its own unique filename.

The database used to test the app is hosted locally. The connection detail in app.py will need to be updated when the website is deployed. There are commands to clear and create the database with all of the tables present in app.py, commented out when not needed.

####  The database:
I settled on using a PostgreSQL database due to increased functionality. While it may not be used to its fullest potential here, if Little Fluffers was deployed in the real world then this option should handle any future developments.

#### The python files:
helpers.py was originally meant to hold some of the functions so that the main app.py would not be quite so cluttered. This fell to the wayside as the project progressed but it still exists as the one function is does hold is used frequently throughout the main file.

app.py is the framework that pulls of this together. The user management aspects were pulled from the CS50 pset Finance. Everything was written in VSCode after hours of downloading and installing languages, libraries, and plugins. The rest was a wonderful, headache-inducing learning experience. The result is a functional webapp that would not have been possible without this course.

Thank you.