package models

import (
	"github.com/jinzhu/gorm"
	"time"
)

type Article struct {
	Model
	TagID int `json:"tag_id" gorm:"index"`
	Tag Tag `json:"tag"`
	Title string `json:"title"`
	Desc string `json:"desc"`
	Content string `json:"content"`
	CreatedBy string `json:"created_by"`
	ModifiedBy string `json:"modified_by"`
	State int `json:"state"`
}

func (article *Article) BeforeCreate(scope *gorm.Scope)error {
	scope.SetColumn("CreatedOn",time.Now().Unix())
	return nil
}
func (article *Article) BeforeUpdate(scope *gorm.Scope) error  {
	scope.SetColumn("ModifiedOn",time.Now().Unix())
	return nil
}

func ExistArticleByID(id int)bool  {
	var article Article
	db.Select("id").Where("id = ?",id).First(&article)

	if article.ID>0{
		return true
	}
	return false

}

func GetArticles(pageNum int,pageSize int,maps interface{})(article []Article)  {
	db.Preload("Tag").Where(maps).Offset(pageNum).Limit(pageSize).Find(&article)
	return 
}

func EditArticle(id int,data interface{})bool  {
	err := db.Model(&Article{}).Where("id = ?",id).Update(data).Error
	if err != nil{
		return true
	}
	return false

}


func GetArticle(id int) (article Article) {
	db.Where("id = ?", id).First(&article)
	db.Model(&article).Related(&article.Tag)
	return
}




func AddArticle(data map[string]interface{})bool  {
	err := db.Create(&Article{
		TagID:data["tag_id"].(int),
		Title:data["title"].(string),
		Desc : data["desc"].(string),
		Content : data["content"].(string),
		CreatedBy : data["created_by"].(string),
		State : data["state"].(int),
	}).Error
	if err!=nil{
		return true
	}
	return false

}


func DeleteArticle(id int) bool {
	db.Where("id = ?", id).Delete(Article{})
	return true
}



