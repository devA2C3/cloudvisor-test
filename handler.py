from datetime import date, datetime     #Date/time manipulation
import boto3                            #Official AWS SDK
import botocore                         #Boto exceptions
import time                             #Time manipulations
import json                             #Json handling
import logging                          #Basic logger
import os                               #File operations


class EC2ETLErrorException(Exception):
    """Raised when EC@ ETL operations fail"""
    pass

def configure_logger():
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def get_region_json_filename(region):
    return region + ".json"

def write_region_json_to_file(region, sorted_instances):
        region_json_file = get_region_json_filename(region)
        with open(region_json_file, 'w') as outfile:
            json.dump(sorted_instances, outfile)

def read_region_json_from_file(filename):
    with open(filename) as json_file:
        return json.load(json_file)

def delete_region_json_file(region):
    filename = get_region_json_filename(region)
    os.remove(filename)

def sanitize_instance_time(instance, key):
    try:
        timestampStr = instance[key].strftime("%d-%b-%Y (%H:%M:%S.%f)")
        instance[key] = timestampStr
    except KeyError:
        #do nothing, not always the key presents
        pass

def sanitize_attach_time(instance):
    try:
        timestampStr = instance["NetworkInterfaces"][0]["Attachment"]["AttachTime"].strftime("%d-%b-%Y (%H:%M:%S.%f)")
        instance["NetworkInterfaces"][0]["Attachment"]["AttachTime"] = timestampStr

        timestampStr = instance["BlockDeviceMappings"][0]["Ebs"]["AttachTime"].strftime("%d-%b-%Y (%H:%M:%S.%f)")
        instance["BlockDeviceMappings"][0]["Ebs"]["AttachTime"] = timestampStr
    except KeyError:
        #do nothing, not always the key presents
        pass

def launch_time_to_epoch(launch_time):
    launch_time_dt_object = datetime.strptime(str(datetime_converter(launch_time)).split("+", 1)[0], '%Y-%m-%dT%H:%M:%S') #Oi vei !!
    return int(time.mktime(launch_time_dt_object.timetuple()))


# Helper to translate AWS datatime to ISO format
def datetime_converter(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type {} is not serializable".format(type(obj)))

def extract_ec2_data(region):
    ec2_client = boto3.client('ec2',region_name=region)
    return ec2_client.describe_instances()

def load_ec2_data(sorted_instances, region):
    write_region_json_to_file(region,sorted_instances)

def transform_ec2_data(json_ec2_list, region):
    if len(json_ec2_list['Reservations']) == 0 :
        logging.warning ("\tNo Ec2 instances found in region {}".format(region))
        return 

    sorted_instances = []
    for reservation in json_ec2_list['Reservations']:
        for instance in reservation['Instances']:
            logging.debug("Adding sortable item - epoch time..")
            instance["epoch_seconds"] = launch_time_to_epoch(instance['LaunchTime'])

            logging.debug("Sanitizing timestamps to make it JSON compatible ..")
            sanitize_instance_time(instance, "LaunchTime")
            sanitize_attach_time(instance)

            logging.debug("Saving transformed instance data..")
            sorted_instances.append(instance)

    sorted_instances.sort(key=lambda k: k['epoch_seconds'], reverse=False)

    for instance in sorted_instances:
        logging.info("\tSorted Instance Id '{}'  Launched at {}".format(instance["InstanceId"], instance["LaunchTime"]))

    return sorted_instances

def ec2_etl(region):
    try:
        logging.debug("Extracting region {} EC2 data..".format(region))
        json_ec2_list = extract_ec2_data(region)

        logging.debug("Transforming region {} EC2 data..".format(region))
        sorted_instances = transform_ec2_data(json_ec2_list,region)

        logging.debug("Loading region {} EC2 data..".format(region))
        load_ec2_data(sorted_instances,region)     

        logging.info("Region {} EC2 ETL task done".format(region))   

    except botocore.exceptions.NoRegionError as ex:
        logging.error (ex)
        raise EC2ETLErrorException
    except (AttributeError, ValueError, KeyError) as ex: 
        logging.error ("Error parsing AWS response for  region {}: {}".format(region,ex))
        raise EC2ETLErrorException
    except (TypeError, IndexError,NameError) as ex: 
        logging.error ("Internal error handling AWS response for region {}: {}".format(region, ex))
        raise EC2ETLErrorException
    except (IOError) as ex: 
        logging.error ("Failed to load region {} data: {}, removing its file to avoid partial results".format(region, ex))
        delete_region_json_file(region)
        raise EC2ETLErrorException

def ec2_data_retrieve(region):
    try:
        json_file_name = get_region_json_filename(region)
        ec2_json = read_region_json_from_file(json_file_name)
        logging.debug("Region {} JSON data is {}".format(region, ec2_json))
    except (IndexError,IOError) as ex: 
        logging.error ("Internal error retrieveing region {} data: {}".format(region, ex))
        return []

    return ec2_json

def main():
    configure_logger()

    try:         
        regions_filename = "regions.txt"
        regions_file = open(regions_filename, 'r') 
        lines = regions_file.readlines()

        for line in lines: 
            region = line.strip()
            try:
                logging.info("Listing EC2 instances in region {}...".format(line.strip())) 
                ec2_etl(region)
            except (EC2ETLErrorException) as ex: 
                logging.error ("Failed to ETL EC2 data from region {}, shit happens, continue to the next region..".format(region))

    except (IOError) as ex: 
        logging.error ("Internal error retrieveing regions list from file: {}".format(regions_filename))


if __name__ == "__main__":
    main()

