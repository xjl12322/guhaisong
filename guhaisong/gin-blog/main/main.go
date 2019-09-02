package main

import (
	"fmt"
	"gin-blog/pkg/setting"
	"gin-blog/routers"
	"github.com/braintree/manners"
	"net/http"
	"time"
)

func main()  {

	router := routers.InitRouter()
	s := manners.NewWithServer(&http.Server{
		Addr:           fmt.Sprintf(":%d",setting.HTTPPort),
		Handler:        router,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	})
	s.ListenAndServe()

	//endless 写法
	//endless.DefaultReadTimeOut = setting.ReadTimeout
	//endless.DefaultWriteTimeOut = setting.WriteTimeout
	//endless.DefaultMaxHeaderBytes = 1 << 20
	//endPoint := fmt.Sprintf(":%d", setting.HTTPPort)
	//server := endless.NewServer(endPoint, routers.InitRouter())
	//server.BeforeBegin = func(add string) {
	//	log.Printf("Actual pid is %d", syscall.Getpid())
	//}
	//err := server.ListenAndServe()
	//if err != nil {
	//	log.Printf("Server err: %v", err)
	//}



	}

