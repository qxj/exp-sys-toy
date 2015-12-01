#!/bin/bash

mysqldump -hlocalhost -uroot -pppzuche exp_sys > exp_sys.sql
scp exp_sys.sql relay00:
