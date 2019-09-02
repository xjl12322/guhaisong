package logging
import (
	"fmt"
	"log"
	"os"
	"time"
)

var (
	LogSavePath = "runtime/logs/"
	LogSaveName = "log"
	LogFileExt = "log"
	TimeFormat = "20060102"
)

func getLogFilePath() string {
	return fmt.Sprintf("%s", LogSavePath)
}

func getLogFileFullPath() string {
	prefixPath := getLogFilePath()
	suffixPath := fmt.Sprintf("%s%s.%s",LogSaveName,time.Now().Format(TimeFormat),LogFileExt)
	return fmt.Sprintf("%s%s", prefixPath, suffixPath)

}

func openLogFile(filePath string) *os.File {
	_, err := os.Stat(filePath)//返回文件信息结构描述文件。如果出现错误，会返回*PathError
	switch {
	case os.IsNotExist(err)://能够得知文件不存在或目录不存在
		mkDir()
	case os.IsPermission(err):  //能够得知权限是否满足
		log.Fatalf("Permission :%v", err)
	}
	handle, err := os.OpenFile(filePath, os.O_APPEND | os.O_CREATE | os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("Fail to OpenFile :%v", err)
	}
	return handle
}

func mkDir()  {
	dir,_ := os.Getwd()
	//创建对应的目录以及所需的子目录，若成功则返回`nil`，否则返回`error`
	err := os.MkdirAll(dir+"/"+getLogFilePath(),os.ModePerm)
	if err != nil {
		panic(err)
	}
}
