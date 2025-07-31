function getSignature(data){
    return CryptoJS.MD5(data).toString();
    
}