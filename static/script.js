//Generating labels for graph(usually for X-axis)
function generateLastMonthLabels(){
    let labels=[];
    let today=new Date();
    for(let i=29;i>=0;i--){
        let d=new Date(today);
        d.setDate(d.setDate()-i);
        labels.push(d.toLocaleDateString('en-US',{day:'numeric',month:'short'})); //formating it in date-month format
    }
    return labels;
}
function generateNext10DaysLabels(){ //For forecasting graphs 
    let labels=[];
    let today=new Date();
    for(let i=1;i<=10;i++){
        let d=new Date(today);
        d.setDate(d.getDate()+i);
        labels.push(d.toLocaleDateString('en-US',{day:'numeric',month:'short'}));
    }
    return labels;
}

//To ensure code runs after HTMLDOM fully loaded
document.addEventListener("DOMContentLoaded",function() {
    const form=document.getElementById("solarform");
    const spinner=document.getElementById("loadingSpinner");

    if(!form){
        console.error("Form element not found!"); 
        return;
    }

form.addEventListener("submit",async function(e) { //to add event listener after submitting
    e.preventDefault();

    const pincode=document.getElementById("pincode").value.trim();  //to fetch user input from form fields
    const tech=document.getElementById("tech").value;
    const area=parseFloat(document.getElementById("area").value);
    const tilt=parseFloat(document.getElementById("tilt").value) || 0;
    const manufacturer=document.getElementById("manufacturer").value || null; 

    if(!pincode || !tech || isNaN(area)){ //to validate required fields
        alert("Please fill in all the required fields");
        return;
    }

    spinner.style.display="block";

    try{
        const response=await fetch("http://127.0.0.1:5000/predict",{ //to send POST request to the backend
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                pincode,
                material:tech,
                area,
                tilt,
                manufacturer,
            }),
        });

        if(!response.ok){
            const error=await response.json();
            throw new Error(error.error || "Prediction failed");
        }

        const data=await response.json();
        console.log("API Response: ",data);
        
        localStorage.setItem("solarPrediction",JSON.stringify(data));
        window.location.href="/results"; //redirects user to results page
    }
    catch(err){ //to handle errors and alert users
        console.error("Error",err.message);
        alert(`${err.message}`);
    }
    finally { //to hide the spinner 
        spinner.style.display="none";
    }
  });
})