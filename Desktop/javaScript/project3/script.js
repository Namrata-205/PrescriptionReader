const imgContainer=document.querySelector(".img-container")
const btnEle =document.querySelector(".btn")

btnEle.addEventListener("click",()=>{
updateImg()
})

function updateImg(){
    const newImg=document.createElement("img")
    newImg.src=`https://picsum.photos/300?random=${Math.floor(Math.random()*10)}`
    imgContainer.appendChild(newImg)
}