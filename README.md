# Cloudvisor Exercise
#### INTRO
Your mission, should you choose to accept it, involves the development of two functions.
A small ETL and an API route (there is no need to implement the API itself). Please read the following instructions before starting to implement your mission, you don't want to miss any important instruction, especially those in [General Guidelines](#general-guidelines).

#### General Guidelines
Your code should be as simple as possible, yet well documented and robust.  

Think about operational use cases from the real world.
Few examples:
1. What happens if things go wrong and code crashes?
1. Remember to reuse code, if applicable
1. Document used packages and versions

#### Ready for action?
Great.  
First, clone this git repo and make a new branch. You’ll find a small boilerplate code to start.

We are going to implement two functions:

###### 1. First function (ETL)
Our mission is to list all EC2 instances (servers) in a particular region of AWS.  
You can use AWS Console for reference.

[Open AWS Console](https://eu-west-1.console.aws.amazon.com/ec2/v2/home?region=eu-west-1#Instances:sort=instanceId)

1. Read the content of regions.txt file into a variable.
1. Use AWS SDK for Python to get a list of existing EC2 instances in the region.
1. Sort the instances by the launch time (provided *datetime_converter* function will help you to convert AWS time object).
1. Save the result (a list of instances) in JSON format to a file. File name should be $region_name.json
1. Now, let’s make this work for more than one region. Change the content of the regions.txt file to:  
us-east-1, eu-west-1, ap-southeast-1

###### 2. Second function (API Route)
This function will be our API route. It will serve the pre-generated list of instances from a file (prepared by our ETL). 

This function gets only one parameter - *region*.  
Returns a list of instances from a file in a valid JSON format.


#### Bonus
For each instance, print the amount of days since it was launched.
