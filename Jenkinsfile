pipeline { 
  agent any  

    stages { 

      stage('Build Env File') {

        steps {

          withCredentials([usernamePassword(credentialsId: 'MYSQL_USER_PASS_1', passwordVariable: 'PASSWORD_1', usernameVariable: 'USERNAME_1')]) {


            writeFile file: './.env', text: """#!/bin/sh
username="${USERNAME_1}" 
password="${PASSWORD_1}" 
db_name="ezcampus_db"
db_port="3306"
db_host="mysql-instance"
              """

          }

        }
      }

      stage('Build Docker Image') { 

        steps { 

          withCredentials([usernamePassword(credentialsId: 'MYSQL_USER_PASS_1', passwordVariable: 'PASSWORD_1', usernameVariable: 'USERNAME_1')]) {

            sshPublisher(
                failOnError: true,
                publishers: [
                sshPublisherDesc(
                  configName: '2GB_Glassfish_VPS',
                  transfers: [
                  sshTransfer(
                    cleanRemote: true,
                    excludes: '',
                    execCommand: '''
                    cd ~/pipeline_datascraper
                    chmod +x build.sh
                    ./build.sh
                    ''', execTimeout: 120000, flatten: false, makeEmptyDirs: true, 
                    noDefaultExcludes: false,
                    patternSeparator: '[, ]+',
                    remoteDirectory: 'pipeline_datascraper',
                    remoteDirectorySDF: false, 
                    removePrefix: '', 
                    sourceFiles: 'env.sh, Dockerfile, requirements.txt, build.sh, deploy.sh, .env, entrypoint.sh, dscrape/**, py_core/**'
                    )
                  ], 
                  usePromotionTimestamp: false,
                  useWorkspaceInPromotion: false,
                  verbose: false)
                    ])
          }
        }
      }
    }
  post {
    always {
      discordSend(
          description: currentBuild.result, 
          enableArtifactsList: false, 
          footer: '', 
          image: '', 
          link: '', 
          result: currentBuild.result, 
          scmWebUrl: '', 
          thumbnail: '', 
          title: env.JOB_BASE_NAME, 
          webhookURL: "${DISCORD_WEBHOOK_1}"
          )
    }
  }
}



