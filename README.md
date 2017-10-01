TheBestest is a project I've casually worked on over the summer to learn about AWS serverless services. I had initially envisioned building a mobile app utilizing an API based on Lambda, API GW, Cognito, and DynamoDB. All services I had never used before. While I did work on developing the API a bit, the project really ended up focusing more of building out a serverless pipeline expanded the project to also leverage CodePipeline, CodeBuild and StepFunction.

Initially I had hoped to use CodePipeline right out of the box, but as I was building things out its shortcomings became apparent. While I would almost certainly be the only one to work on TheBestest, I wanted to create a pipeline that could handle multiple developers and multiple parallel feature branches. CodePipeline was limited to pulling directly from GitHub form a single predefined branch. This didn't work well in the scenario I wanted to plan for.

So I worked on a PipelineMgr that extended CodePipeline's functionality with Lambda and StepFunction, which works something like this:

1. **Webhook from Github** is sent to an API GW when a PR is opened or updated. The API GW takes the webhook post and re-formats it into an API request to StepFunction. As an aside here, during development I was creating and tearing down the CloudFormation Stack that created the API GW. This would mean the webhook endpoint URL would be changing frequently. So as part of the pipeline deploy script (deploy_pipeline.py) I would automatically retrieve the new API GW URL and update the webhook endpoint URL in GitHub.
2. **StepFunction** would receive the API call from API GW and kick of a series of Lambdas that managed the flow of the PR through the pipeline. The first being a Lambda that would download a zipball of the repo from GitHub based on the commit SHA sent in the webhook and then upload it to S3. This zipball would be used by CodePipeline instead of going directly to GitHub and allowed supporting multiple PRs/feature branches. The zipball downloaded by the Lambda was orginized slightly different than what was expected by CodeBuild, so the Lambda repackaged the zipball before uploading it to S3.
3. **CodePipeline for UnitTesting** run would be started by a Lambda kicked off by StepFunction. This would leverage CodeBuild to build a unit test environment for TheBestest App. This involved downloading and running a [local DynamoDB instance](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html), prepping the DynamoDB instance with test data and then running the unit tests for the TheBestest App code. Additionally the CloudFormation template to deploy TheBestest App would be validated.
4. **StepFunction** uses a Lambda that polls the UnitTest CodePipeline for it's status. A Lambda updates the PR's status with the status of the UnitTest CodePipeline run when it completes. Assuming the run is successful then the Deploy Pipeline is started.
5. **CodePipeline for Deploy** is used to build or update TheBestest App CloudFormation stack. CodeBuild is used to do a CloudFormation package of the template and that output template is used to create and execute a change set. While all changes are deployed into a single environment, which I'm calling stage for now, the idea would be that every PR/feature branch would get it's own environment. So, the Pipeline for unit testing and deploy are separate as I envision multiple deploy pipelines. A deploy pipeline being spun up and down as PRs are opened and closed.
6. **StepFunction** uses a Lambda that pools the Deploy Pipeline and reports back the status in a similar fashion with the UnitTest Pipeline.

In addition to the Lambdas used in the PipelineMgr, another Lambda is used to deploy updates to the API GW's stage (both for the PipelineMgr Webhook endpoint and TheBestest App API endpoint). This lambda is called as a CloudFormation custom resource. This is needed as when there are changes to an API GW config, that config needs to be deployed into something called a stage. While CloudFormation does have a API GW Stage and Deploy resource, they really only work well for an inital creation and not for updating an existing API GW. To get around this I created the Custom Resource backed by a Lambda that does the deployment in a more reliable manner.

An overview and highlight of the repo is as follows:

* **deploy** directory contains the CloudFormation Template for TheBestest App and a deployment script (only intended to be used for quick and dirty testing as deploys should normally do through the pipeline).
* **functions** directory contains the code for the Lambda functions that are part of TheBestest App (a whole whopping one right now) and their unit tests.
* **pipeline** contains code to deploy and run the pipelines.
  * **functions** includes code used for PipelineMgr and API GW stage deployer Lambdas.
  * **deploy_pipeline.py** script used to deploy pipelines based on the CloudFormation templates found in the same directory (templates end with _stack.yaml)
* **testing** scripts and config needed to initialize the unit testing environment.








