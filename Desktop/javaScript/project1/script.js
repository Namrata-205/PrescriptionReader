const button=document.querySelectorAll(".box")
const body=document.querySelector("body")

button.forEach(function(box){
    box.addEventListener("click",function(color){
        if(color.target.id ==="box1"){
            body.style.backgroundColor="rgb(225, 96, 96)"
        }
        else if(color.target.id ==="box2"){
            body.style.backgroundColor="palegreen"
        }
        else if(color.target.id ==="box3"){
            body.style.backgroundColor="chartreuse"
        }
        else if(color.target.id ==="box4"){
            body.style.backgroundColor="coral"
        }
        else if(color.target.id ==="box5"){
            body.style.backgroundColor="crimson"
        }
    })
})