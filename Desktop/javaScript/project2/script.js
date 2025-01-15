const textArea=document.getElementById("textarea")
const totalchar=document.getElementById("total-char")
const remchar=document.getElementById("remaining-char")

textArea.addEventListener("keyup",()=>{
    updateCounter()
})

function updateCounter(){
    totalchar.innerText=textArea.value.length

    remchar.innerText=textArea.getAttribute("maxlength")-textArea.value.length
}
