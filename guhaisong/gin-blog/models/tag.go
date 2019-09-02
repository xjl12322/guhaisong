package models

import (
	"github.com/jinzhu/gorm"
	"log"
	"time"
)

type Tag struct {
	Model
	Name string `json:"name"`
	CreatedBy string `json:"created_by"`
	ModifiedBy string `json:"modified_by"`
	State int `json:"state"`

}


func GetTags(pageNum int,pageSize int,maps interface{})(tags []Tag)  {
	db.Where(maps).Offset(pageNum).Limit(pageSize).Find(&tags)
	return
}

func GetTagTotal(maps interface{})(count int)  {
	db.Model(&Tag{}).Where(maps).Count(&count)
	return
}

func ExistTagByName(name string) bool  {
	var tag Tag
	db.Select("id").Where("name=?",name).First(&tag)
	if tag.ID>0{
		return true
	}
	return false
}

func ExistTagByID(id int)bool  {
	var tag Tag
	db.Select("id").Where("id = ?",id).First(&tag)
	if tag.ID > 0{
		return true
	}
	return false


}

func AddTag(name string,state int,createdBy string) bool {
	result := db.Create(&Tag{
		Name:name,
		State:state,
		CreatedBy:createdBy,
	})
	err := result.Error
	if err != nil{
		log.Println("添加数据库异常")
		return false
	}
	return true
}
func DeleteTag(id int)bool  {
	err := db.Where("id = ?",id).Delete(&Tag{}).Error
	if err != nil{
		log.Println("删除数据库异常")
		return false
	}
	return true

}



func EditTag(id int,data map[string]interface{})bool  {
	err := db.Model(&Tag{}).Update("id = ?",id).Update(data).Error
	if err!= nil{
		log.Println("编辑失败",err)
	}
	return true
}



func (tag *Tag) BeforeCreate(scope *gorm.Scope) error  {
	scope.SetColumn("CreatedOn",time.Now().Unix())
	return nil
}


func (tag *Tag) BeforeUpdate(scope *gorm.Scope) error  {
	scope.SetColumn("ModifiedOn",time.Now().Unix())
	return nil
}








