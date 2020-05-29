# Private newsletter

This project will generate your own newsletter and send you one instance of it every time you call it.

## Getting Started

You will have to build a secret file containing your email server informations. You have to create and fill out the file "secret.py" like so :

```
sender_email = "sender@gmail.com"
receiver_email = "your.email@gmail.com"
password = "yourVerySecurePassword"
```

### Test

To test the building of the newsletter without sending it you can do :

```
pipenv install
pipenv shell
./sendInstance.py --test
```

This will create an html file in the folder containing your personalized newsletter.

## Automating

You can automatically send the newsletter using cron and the launch script ("launch.sh"). The script is designed to be able to work even on a computer that is not always turned on. As such I configure cron to call the script every hours and the script manages itself to figure out if it sent his newsletter today yet or if it need to do it now.

```
0 * * * *     /bin/bash /home/karlito/creation/mailingList/launch.sh
```
