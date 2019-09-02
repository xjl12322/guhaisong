package routers

import (
	"gin-blog/middleweare/jwt"
	"gin-blog/pkg/setting"
	"gin-blog/routers/api"
	"gin-blog/routers/api/v1"
	"github.com/gin-gonic/gin"
)



func InitRouter() *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(),gin.Recovery())
	gin.SetMode(setting.RunMode)


	r.GET("auth",api.GetAuth)  //获取token接口
	apiv1 := r.Group("/api/v1")
	apiv1.Use(jwt.JWT())
	{   //标签的crud
		apiv1.POST("/tags",v1.AddTag)
		apiv1.DELETE("/tags",v1.DeleteTag)
		apiv1.PUT("/tags",v1.EditTag)
		apiv1.GET("/tags",v1.GetTag)

		//获取文章列表
		apiv1.GET("/articles", v1.GetArticles)
		//获取指定文章
		apiv1.GET("/articles/:id", v1.GetArticle)
		//新建文章
		apiv1.POST("/articles", v1.AddArticle)
		//更新指定文章
		apiv1.PUT("/articles/:id", v1.EditArticle)
		//删除指定文章
		apiv1.DELETE("/articles/:id", v1.DeleteArticle)



	}

	return r


}