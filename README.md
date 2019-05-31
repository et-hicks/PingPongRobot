## Ping Pong Robot:
======
All production code

This is highly specific code to make a robot with two cameras move.

There are hard coded numbers, repeated code, few functions.

The code is ugly and disgusting. Please do not judge.

# Setup:
------
It requires two cameras perpendicular to each other. In the python file, there are three global variables, labeled A, B, C. These are measured in decimeters. From A, B, C, you will choose the X, Y, Z (0,0,0) origin point. A is the distance from the origin to the camera that will measure (Y, Z) coordinates. B is the distance from the origin to the camera that will measure (X, Z) coordinates. C is the distance from the floor to the height of the cameras. It is imperitive that the cameras are the same height for accurate prediction.

The robot relies on computer vision to work properly. As such, the room must be devoid of all color, besides the color of the ball being tracked. The code currently has it hard coded in to be a nice teal color. As such, there must be no teal in the room with the cameras.

# Code:
------
The microcontroller code is main.c and is located within Timertesting/Timertesting.cydsn/main.c. The code is intended for a Cypress PSoc kit, specifically the [CY8CKIT-059](https://www.cypress.com/documentation/development-kitsboards/cy8ckit-059-psoc-5lp-prototyping-kit-onboard-programmer-and). This MCU is intended to be hooked up to the computer that is running the main python file, called withCapture(1).py. In our set-up, we programmed the PSoC first, then began the python file. If done correctly, there will be a bootup process that is the robot going to the X coordinate of the located camera.

The python code requires many libraries to be installed and added to work properly. If one of these libraries is not installed, or the PSoC is not plugged into the computer, or if the USB port the PSoC is using is already connedted to somthing else, then the code will either error out immediatly, or will error out when it comes to a library that is not installed. The python code is ugly and loooong, but it works.

# Demo
------
A demo of the robot can be found here. It works, but by the nature of computer vision tracking a color, it is a little off sometimes.


# Thanks:
The same version of the code can be found [here](https://github.com/CaesarLinxw/ME135). This github account is owned by the other major software engineer of the project. I have more commits on his profile because we used his laptop as the working laptop of the project as it was the most powerful we had access too. In addition, we did not begin using github until much later in the project, leading to us trading code and causing many duplicate files. Using him as the main working laptop meant most of the development and most of the commits came from that computer. This is bad practice, and I will never do this again. It was a pain working with such messy code, using a messy system.
