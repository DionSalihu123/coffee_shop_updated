def get_response(user_message):

    responses = {
            "hello" : "Hi there! How can I help you?",
            "hi" : "Hi there! How can I help you?", 
            "who created the website" :  "The coffee shop website was created by Dion Salihu and Behar Mahmuti.",
            "what is in the offer today" : "Today's offer includes:Esspresso,mocha,latte",
            "what do you recommand" : "I recommand latte!",
            "what are the prices" : "Esprsso : 3.00$, Mocha : 5.00$,Americano : 3.00$",
            "where does the coffee shop opens" : "The coffee shop open's in 8:00am !",
            "where does the coffee shop closes" : "The coffee shop close's at  11:00pm !",
            "how can i create an account" : "click in the login button and select register now!" 

            }

    return  responses.get(user_message.lower(), "I'm not sure about that. Can you ask differently?")
 
