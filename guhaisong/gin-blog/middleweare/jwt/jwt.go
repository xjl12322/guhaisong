package jwt

import (
	"gin-blog/pkg/e"
	"gin-blog/pkg/util"
	"github.com/gin-gonic/gin"
	"net/http"
	"time"
)

func JWT()gin.HandlerFunc{  //鉴权验证中间件
	return func(c *gin.Context) {
		var code int
		var data interface{}
		code = e.SUCCESS
		token := c.Query("token")
		if token == "" {
			code = e.INVALID_PARAMS
		}else{
			claims, err := util.ParseToken(token)
			if err != nil{
				code = e.ERROR_AUTH_CHECK_TOKEN_FAIL
			}else if time.Now().Unix() > claims.ExpiresAt{
				code = e.ERROR_AUTH_CHECK_TOKEN_TIMEOUT
			}
		}
		if code != e.SUCCESS{
			c.JSON(http.StatusUnauthorized,gin.H{
				"code":code,
				"msg":e.GetMsg(code),
				"data":data,
			})
			c.Abort()
			return
		}
		c.Next()



	}
}


















