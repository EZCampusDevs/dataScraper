pipeline { 
    agent any  

     tools {
            maven 'maven3'
            jdk 'OpenJDK17'
    }
    
    stages { 
        
        stage('Copy Repo To Remote') { 
            steps { 
                
                sh 'ls -la'
                
                    sshPublisher(publishers: [
                        sshPublisherDesc(configName: '2GB_Glassfish_VPS', transfers: [
                            sshTransfer(cleanRemote: false, excludes: '', execCommand: '', execTimeout: 120000, flatten: false, makeEmptyDirs: false, 
                            noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: './pipline_datascraper', remoteDirectorySDF: false, 
                            removePrefix: '', sourceFiles: 'dataScraper')
                        ], 
                        usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)
                    ])
            }
        }
    }
}
