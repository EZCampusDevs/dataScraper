pipeline { 
    agent any  

    stages { 
        
        stage('Build Docker Image') { 
            steps { 

                    sshPublisher(
                        failOnError: true,
                        publishers: [
                        sshPublisherDesc(configName: '2GB_Glassfish_VPS', transfers: [
                            sshTransfer(cleanRemote: true, excludes: '', execCommand: '''
                            cd ~/pipeline_datascraper
                            chmod +x build.sh
                            ./build.sh
                            ''', execTimeout: 120000, flatten: false, makeEmptyDirs: true, 
                            noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: 'pipeline_datascraper', remoteDirectorySDF: false, 
                            removePrefix: '', sourceFiles: 'Dockerfile, requirements.txt, build.sh, deploy.sh, .env, entrypoint.sh, dscrape/**')
                        ], 
                        usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)
                    ])
            }
        }
    }
}


