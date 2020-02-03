
# Radhika Zawar - Master of Data Science @RMIT
# Under the guidance of Dr Vic Ciesielski
#
# This file has a python script developed for RMIT in-house project under the School of Science and Technology
#
# This script is written to utilise high level output generated by aws rekognition
# aws rekognition has ability to detect things present in the image using deep leaning algorithms.
# It can also provide confidence interval for detected label
# In this Script, I have fetched images from AWS S3 and sent them to AWS rekognition, one by one.
# The detected labels are saved in the database - AWS dynamodb
#
#
# references: https://docs.aws.amazon.com/rekognition/latest/dg/what-is.html
#             https://docs.aws.amazon.com/AmazonS3/latest/dev/Welcome.html
#             https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html
#
#
# part 1 - house price prediction using image data - image label detection

import boto3
import csv

"""
This is a very sophisticated code for reading IAM credential file from local machine
this user has permissions for AmazonS3FullAccess, AmazonDynamoDBFullAccess
AmazonRekognitionFullAccess
"""
with open ('credentials.csv', 'r') as input:
    next(input)
    reader = csv.reader(input)
    for line in reader:
        access_key_id = line[2] #third column has access key
        secret_access_key = line[3] #fourth column has secret access key

"""Please note, these credential must not be shared to any one for the matter of safety"""


"""
following function is designed to detect labels of the image by passing it to aws Rekognition
this opens the s3 bucket, loads the image to aws rekognition and fetches back all the tags
"""
def detect_labels(bucket, key, max_labels=15, min_confidence=50, region="ap-southeast-2"):
    #creating rekognition client
	rekognition = boto3.client("rekognition", region_name='ap-southeast-2',
                            aws_access_key_id = access_key_id,
                            aws_secret_access_key = secret_access_key)
    # fetching image from s3 bucket and loading it to rekognition and detecting labels
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	return response['Labels']


"""
following commands are dealing with aws dynamodb
I have created a client object to access the specified table
"""
dynamodb = boto3.resource('dynamodb',region_name='ap-southeast-2',
                    aws_access_key_id = access_key_id,
                    aws_secret_access_key = secret_access_key)
table = dynamodb.Table('dummy_image_labels')


"""
Accessing data from AWS S3
and passing it to aws rekognition
fetching all the tags
saving it into dynamoDb
"""
bucket = 'dummyimagebucket'     #Specify bucket name


#Creating s3 client
s3 = boto3.resource('s3',region_name='ap-southeast-2',
                    aws_access_key_id = access_key_id,
                    aws_secret_access_key = secret_access_key)

#fetching s3 bucket
my_bucket = s3.Bucket('dummyimagebucket')

#retrieving objects from the bucket
for my_bucket_object in my_bucket.objects.all():
    photo = my_bucket_object.key    # key specifies image_name
    list = []                       # an empty list is created for every new image to save labels for intermediate step

    # calling detect label function, which passes image to aws rekognition and brings back the labels
    # adding each label to the list
    for label in detect_labels(bucket, photo):
        tag = "{Name} - {Confidence}%".format(**label)  # getting it into the desirable format
        list.append(tag)                                # appending labels to the list

        # for command creates an entry inside DynamoDB database
        # this data is stored in the following format
        #   { image_names    ->  list of labels [ label : confidence ] }
        table.put_item(
           Item={
                'image_names': photo,
                'labels':list
            }
        )
