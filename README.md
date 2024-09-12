# AzPythonTweetBot
A New York Times automatic tweet bot which has a goal to tweet every new article posted in 5 minute intervals in the US section of NYT using cronjobs. Connected to an Azure Cosmos DB. https://twitter.com/NYTimesXBot

Some of the coding decisions I made are as a result of this being a complete personal deployment since this project is soley created and handled by myself.


## Overview of the infrastructure that gets created when this repo is executed for the first time 

![Twitter Infrastructure Diagram](https://github.com/user-attachments/assets/fda00ff5-1b9e-45e7-8bb3-9622ae301581)



## Docker Implementation
I was going to just make a fork of this repo for my dockerized implementation of this project but that's unfortunately not possible since I'm the owner.
- The dockerized repo of this project can be found [here](https://github.com/AllenShap/Dockerized-AzPythonTweetBot)
- The dockerized version changes the project to use a selfhosted API instead of local .txt files, changes some of the logic of the bot to accomodate the API implementation, and implements a VPN for added complexity to the project for fun.
