import json
import boto3

dynamodb = boto3.client('dynamodb')
table_name = 'MyTable'
key_schema = [
    {
            'AttributeName': 'UserId',
            'KeyType': 'HASH'
    },
    {
            'AttributeName': 'GameTitle',
            'KeyType': 'RANGE' 
    }
    ]
attribute_definitions = [
    {
            'AttributeName': 'UserId',
            'AttributeType': 'S'  # String type
    },
    {
            'AttributeName': 'GameTitle',
            'AttributeType': 'S'  # String type
    }
    ]
provisioned_throughput = {
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
}

def lambda_handler(event, context):
    # TODO implement
    # Create the table
    # Define the table name and schema
    # Initialize a session using Amazon DynamoDB

    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            ProvisionedThroughput=provisioned_throughput
        )
        print("Table created successfully!")
        print("Table status:", response['TableDescription']['TableStatus'])
    except Exception as e:
        print("Error creating table:", e)
        
    try:
        res = dynamodb.describe_table(
            TableName='arn:aws:dynamodb:us-east-1:288761748778:table/MyTable'
            )
        print('Describe Table: ', res)
    except Exception as e:
        print('Error at describe table request: ', e)

    return {
        'status_code':200,
        'response': 'OK'
        
    }
