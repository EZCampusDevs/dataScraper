pipeline { 
    agent any  

     tools {
            maven 'maven3'
            jdk 'OpenJDK17'
    }

    stages { 
        
        stage('Copy Repo To Remote') { 
            steps { 

                    sshPublisher(publishers: [
                        sshPublisherDesc(configName: '2GB_Glassfish_VPS', transfers: [
                            sshTransfer(cleanRemote: true, excludes: '', execCommand: '', execTimeout: 120000, flatten: false, makeEmptyDirs: true, 
                            noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: 'pipline_datascraper', remoteDirectorySDF: false, 
                            removePrefix: '', sourceFiles: 'Dockerfile, requirements.txt, build.sh, deploy.sh, .env, entrypoint.sh, dscrape/**')
                        ], 
                        usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)
                    ])
            }
        }
    }
}

