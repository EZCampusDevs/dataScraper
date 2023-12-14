/*
 * Copyright (C) 2022-2023 EZCampus 
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

pipeline { 
  agent any  

    stages { 

      stage('Build Docker Image') { 

        steps { 

            sshPublisher(
                failOnError: true,
                publishers: [
                sshPublisherDesc(
                  configName: "${SSH_SERVER}",
                  transfers: [
                  sshTransfer(
                    cleanRemote: true,
                    excludes: '',
                    execCommand: '''
                    cd ~/pipeline_datascraper
                    chmod +x build.sh
                    ./build.sh USE_LOG_FILE
                    ''', execTimeout: 120000, flatten: false, makeEmptyDirs: true, 
                    noDefaultExcludes: false,
                    patternSeparator: '[, ]+',
                    remoteDirectory: 'pipeline_datascraper',
                    remoteDirectorySDF: false, 
                    removePrefix: '', 
                    sourceFiles: 'Dockerfile, requirements.txt, build.sh, entrypoint.sh, dscrape/**, py_core/**'
                    )
                  ], 
                  usePromotionTimestamp: false,
                  useWorkspaceInPromotion: false,
                  verbose: false)
                    ])
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



