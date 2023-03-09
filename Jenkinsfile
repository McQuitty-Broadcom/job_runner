pipeline {
    agent any
    environment {
        // z/OSMF Connection Details
        ZOWE_OPT_HOST="mstrsvw.lvn.broadcom.net"
    }
    stages {
        stage('local setup') {
            steps {
                bat 'node --version'
                bat 'npm --version'
                bat 'zowe --version'
                bat 'npm install'
            }
        }
        stage('set1') {
            steps {
                //ZOWE_OPT_USERNAME & ZOWE_OPT_PASSWORD are used to interact with Endevor 
                withCredentials([usernamePassword(credentialsId: 'eosCreds', usernameVariable: 'ZOWE_OPT_USER', passwordVariable: 'ZOWE_OPT_PASSWORD')]) {
                    bat 'gulp --ds mcqth01.jcl.ex --dir job1 --maxrc 0'
                }
            }
        }
        stage('set2') {
            steps {
                //ZOWE_OPT_USER & ZOWE_OPT_PASSWORD are used to interact with z/OSMF and CICS
                withCredentials([usernamePassword(credentialsId: 'eosCreds', usernameVariable: 'ZOWE_OPT_USER', passwordVariable: 'ZOWE_OPT_PASSWORD')]) {
                    bat 'gulp --ds mcqth01.jcl.ex2 --dir job2 --maxrc 4'
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '**/*.txt', followSymlinks: false
            cleanWs()
        }
    }
}