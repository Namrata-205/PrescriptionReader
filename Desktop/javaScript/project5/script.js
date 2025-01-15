const btnsEle=document.querySelectorAll("button")

const inputEle=document.getElementById("result");

for(let i=0;i<btnsEle.length;i++)
{
    btnsEle[i].addEventListener("click",()=>{
        const btnval=btnsEle[i].textContent;
        if(btnval==="C")
        {
            clearResult()
        }
        else if(btnval==="=")
        {
            calculateResult()
        }
        else{
            appendValue(btnval)
        }
    })

}
function clearResult(){
    inputEle.value=""
}

function calculateResult(){
    inputEle.value=eval(inputEle.value)
}

function appendValue(btnval){
    inputEle.value += btnval
}