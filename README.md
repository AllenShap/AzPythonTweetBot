# AzPythonTweetBot (WIP)
A New York Times automatic tweet bot which has a goal to tweet every new article posted in 5 minutes update intervals in the US section of NYT using cronjobs. Connected to an Azure Cosmos DB.

I plan to dockerize this and also integrate it with Kubernetes. Each function of the program is aimed to be in it's own Docker/Kubernetes container in order to decouple it as much as possible and to purposely over-complicate it for the sake of learning.

Goals for the project:
1. Make it into an Azure Function App so it does not have to be run locally.(99% complete as of 3/19/2024(ironing out bugs/anomalies)
2. Make a Terraform deployment for the Azure Function App. (100% functionally complete as of 3/19/2024(although I will probably end up making small changes from here on out to it)
3. Complete the CI/CD pipeline for more or less a 1 click deployment from scratch if the whole infrastructure were to be destroyed.(100% complete as of 3/25/2024(just needed to change the execution of both workflow actions from workflow_dispatch)

Complicated part:
1. Seperate the functions into their own files so each function is in it's own Docker container and the end goal is still achieved. (not started)
   - Do the same thing for Kubernetes which would have a cluster with each function in it's own pod or container. (perhaps using Argo Workflows and AKS)  (not started)


Optional Goals:
1. Deploy the project using Helm/Ansible/Jenkins. (not started)
2. Modify Python Function app so that the timestamp for the tweets is not as obnoxious.(100% complete as of 3/25/2024)
3. Modify Python Function app so that whenever a news article title is changed; it's clearly stated that the news article was changed instead of simply tweeting out the article again with a new title. (about 50% done and 50% accurate with tweeting the article - testing this in my other personal github account as this one is meant to be somewhat "professional" appearing)

Some of the coding decisions I made are as a result of this being a complete personal deployment since this project is soley created and handled by myself.
