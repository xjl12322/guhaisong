package util

import (
	"gin-blog/pkg/setting"
	"github.com/dgrijalva/jwt-go"
	"time"
)
//生成jwt

//Playload(载荷又称为Claim)

var jwtScecret = []byte(setting.JwtSecret)

type Claims struct {
	Username string `json:"username"`
	Password string `json:"password"`
	jwt.StandardClaims
}

func GenerateToken(username,password string)(string,error)  {
	nowTime := time.Now()
	expireTime := nowTime.Add(3*time.Hour)

	claims := Claims{
		username,
		password,
		jwt.StandardClaims{
			ExpiresAt:expireTime.Unix(),
			Issuer:"gin-blog",
		},
	}
	tokenClaims := jwt.NewWithClaims(jwt.SigningMethodHS256,claims)
	token,err := tokenClaims.SignedString(jwtScecret)
	return token,err

}

func ParseToken(token string)(*Claims,error)  {
	tokenClaims,err:= jwt.ParseWithClaims(token,&Claims{}, func(token *jwt.Token) (i interface{}, e error) {
		return jwtScecret,nil
	})

	if tokenClaims != nil{
		if claims,ok := tokenClaims.Claims.(*Claims); ok && tokenClaims.Valid{
			return claims,nil
		}
	}
	return nil,err
	
}


























