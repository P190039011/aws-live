from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

# DBHOST = os.environ.get("DBHOST")
# DBPORT = os.environ.get("DBPORT")
# DBPORT = int(DBPORT)
# DBUSER = os.environ.get("DBUSER")
# DBPWD = os.environ.get("DBPWD")
# DATABASE = os.environ.get("DATABASE")

bucket= custombucket
region= customregion

db_conn = connections.Connection(
    host= customhost,
    port=3306,
    user= customuser,
    password= custompass,
    db= customdb
    
)
output = {}
table = 'student';

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com');
@app.route("/addemp", methods=['POST'])
def AddEmp():
    regid = request.form['reg_id']
    full_name = request.form['full_name']
    cert_name = request.form['cert_name']
    veri_num = request.form['veri_num']
    spl_name = request.form['spl_name']
    crt_pdf_file = request.files['crt_pdf_file']
  
    insert_sql = "INSERT INTO student VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if crt_pdf_file.filename == "":
        return "Please select a file"

    try:
        
        cursor.execute(insert_sql,(reg_id, full_name, cert_name, veri_num, spl_name))
        db_conn.commit()
        stdnt_name = "" + first_name 
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "reg-id-"+str(reg_id) + "_pdf_file"
        s3 = boto3.resource('s3')

        
        
        try:
            print("Data inserted in MySQL RDS... uploading pdf to S3...")
            s3.Bucket(custombucket).put_object(Key=crt_pdf_file_name_in_s3, Body=crt_pdf_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                crt_pdf_file_name_in_s3)

            # Save image file metadata in DynamoDB #
            print("Uploading to S3 success... saving metadata in dynamodb...")
        
            
            try:
                dynamodb_client = boto3.client('dynamodb', region_name= customregion )
                dynamodb_client.put_item(
                 TableName= customtable,
                    Item={
                     'stdntid': {
                          'N': stdnt_id
                      },
                      'pdf_url': {
                            'S': object_url
                        }
                    }
                )

            except Exception as e:
                program_msg = "Flask could not update DynamoDB table with S3 object URL"
                return str(e)
        
        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=stdnt_name)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("GetEmp.html")


@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    reg_id = request.form['reg_id']

    output = {}
    select_sql = "SELECT reg_id, full_name, cert_name, veri_num, spl_name from student where reg_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql,(reg_id))
        result = cursor.fetchone()

        output["reg_id"] = result[0]
        print('EVERYTHING IS FINE TILL HERE')
        output["full_name"] = result[1]
        output["cert_name"] = result[2]
        output["veri_num"] = result[3]
        output["spl_name"] = result[4]
        print(output["reg_id"])
        dynamodb_client = boto3.client('dynamodb', region_name=customregion)
        try:
            response = dynamodb_client.get_item(
                TableName= customtable ,
                Key={
                    'empid': {
                        'N': str(emp_id)
                    }
                }
            )
            pdf_url = response['Item']['pdf_url']['S']

        except Exception as e:
            program_msg = "Flask could not update DynamoDB table with S3 object URL"
            return render_template('addemperror.html', errmsg1=program_msg, errmsg2=e)

    except Exception as e:
        print(e)

    finally:
        cursor.close()

    return render_template("GetEmpOutput.html", id=output["reg_id"], fname=output["full_name"],
                           cname=output["cert_name"], verificationnum=output["veri_num"], specilization=output["spl_name"],
                           image_url=image_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)
