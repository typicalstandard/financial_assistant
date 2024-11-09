
CREATE TABLE account(
    id SERIAL PRIMARY KEY,
    Телефон varchar(30) UNIQUE NOT NULL,
    Пароль varchar(30)

);


CREATE  TABLE  mcc_bank(
    id SERIAL PRIMARY KEY,
    Примечание varchar(105),
    MCC int,
    Категория text


);

CREATE TABLE bank_statement(
    id SERIAL PRIMARY KEY,
    Дата varchar(10),
    Примечание varchar(105),
    Сумма_в_валюте_счета varchar(50),
    Сумма_в_валюте_операции varchar(50),
    account_id int,
    FOREIGN KEY (account_id) REFERENCES account (id)
  
#денормализация для обработки данных 
CREATE TABLE finally_statement AS
SELECT Дата,Примечание,MCC,Категория,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id
FROM bank_statement
 INNER JOIN mcc_bank USING (Примечание)
WHERE bank_statement.Примечание IS NOT NULL AND bank_statement.Дата IS NOT NULL
ORDER BY Дата;
