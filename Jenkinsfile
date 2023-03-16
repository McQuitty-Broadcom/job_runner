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
                bat 'python -m pip install argparge'
                bat 'python -m pip install json'
            }
        }
        stage('set1') {
            steps {
                //ZOWE_OPT_USERNAME & ZOWE_OPT_PASSWORD are used to interact with Endevor 
                withCredentials([usernamePassword(credentialsId: 'eosCreds', usernameVariable: 'ZOWE_OPT_USER', passwordVariable: 'ZOWE_OPT_PASSWORD')]) {
                    bat 'python job_runner_json --ds config.json -o python_jobs'
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