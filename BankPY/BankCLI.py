from decimal import Decimal
from datetime import date, datetime, timedelta
import pickle
import io
import time
import logging
from sqlalchemy import Column, Boolean, Float, Integer, Unicode, UnicodeText, String, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship, backref, declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class BankCLI:
    def run():
        bank = Bank("Bank of Python")
        selectedAccount = None
        currentDate = date.today().strftime("%Y-%m-%d")
        saveFileName = "bank.pickle"
        
        while(True):
            print("--------------------------------")
            if(selectedAccount == None):
                print("Currently selected account:", None)
            else:
                print("Currently selected account:", selectedAccount.toString())
            print("Enter command")
            print("1: open account")
            print("2: summary")
            print("3: select account")
            print("4: list transactions")
            print("5: add transaction")
            print("6: interest and fees")
            print("7: save")
            print("8: load")
            print("9: quit")
            ip = input(">")

            try: 
                if(ip == '1'):
                    accType = input("Type of account? (checking/savings)\n>")

                    while(True):
                        try:
                            if (accType == "savings" or accType == "s"):
                                bank.addAccount(False, Decimal(input("Initial deposit amount?\n>")))
                            else:
                                bank.addAccount(True, Decimal(input("Initial deposit amount?\n>")))
                            break;
                        except:
                            print("Please try again with a valid dollar amount.")

                    logging.debug("Created account: " + str(bank._index - 1))
                elif (ip == '2'):
                
                    for acc in bank._accounts:
                        acc.printAccount()

                elif (ip == '3'):
                    idx = int(input("Enter account number\n>"))

                    #Ensures that we don't attempt to call an account that doesn't yet exist
                    if(idx - 1 < bank._index):
                        selectedAccount = bank._accounts[idx - 1]

                elif (ip == '4'):
                    for t in selectedAccount._transactions:
                        t.printTransaction()

                elif (ip == '5'):
                    while(True):
                        try:
                            amount = Decimal(input("Amount?\n>"))
                            break
                        except:
                            print("Please try again with a valid dollar amount.")

                    dt = None
                    while(True):
                        try:
                            dt = datetime.strptime(input("Date? (YYYY-MM-DD)\n>"), "%Y-%m-%d").date()
                            break
                        except ValueError:
                            print("Please try again with a valid date in the format YYYY-MM-DD.")
                        
                    try:
                        selectedAccount.addTransaction(Transaction(dt, amount, False), 1)
                    except OverdrawError:
                        print("This transaction could not be completed due to an insufficient account balance.")
                    except TransactionSequenceError as e:
                        print("New transactions must be from", e.lastDate.strftime("%Y-%m-%d"), "onward.")
                    except TransactionLimitError as e:
                        print("This transaction could not be completed because this account already has", e.error)

                    

                elif (ip == '6'):
                    try:
                        selectedAccount.addInterest()
                    except TransactionSequenceError as e:
                        print("Cannot apply interest and fees again in the month of", e.lastDate.strftime('%B') + ".")
                    
                    logging.debug("Triggered fees and interest")

                elif (ip == '7'):
                    saveFile = open(saveFileName, 'wb')
                    pickle.dump(bank, saveFile)
                    logging.debug("Saved to " + saveFileName)

                elif (ip == '8'):
                    saveFile = open(saveFileName, 'rb')
                    bank = pickle.load(saveFile)
                    logging.debug("Loaded from " + saveFileName)

                elif (ip == '9'):
                    break
            except AttributeError as e:
                print(repr(e))
                print("This command requires that you first select an account.")
            

class Bank(Base):

    __tablename__ = "bank"
    _id = Column(Integer, primary_key=True)
    _index = Column(Integer)
    _name = Column(String)
    _accounts = relationship("Account", backref = backref("bank"))

    def __init__(self, name):
        self._index = 1;
        self._name = name;

    def addAccount(self, checkings, initialDeposit):
        """
        Creates a new account for this bank.
        checkings - Boolean value. True is the account to be made is a checking account, False otherwise (savings account)
        initialDeposit - The initial amount of money to be transacted into the newly made account.
        """
        if (checkings):
            n = CheckingAccount(initialDeposit, self._index)
            self._accounts.append(n)
            #session.add(n)
        else:
            n = SavingsAccount(initialDeposit, self._index)
            self._accounts.append(n)
            #session.add(n)
        self._index += 1

class Account(Base):

    __tablename__ = "account"

    _index = Column(Integer, primary_key=True)
    _bankIndex = Column(Integer, ForeignKey("bank._id"))
    _balance = Column(Float)
    _transactions = relationship("Transaction", backref = backref("account"))
    _type = Column(String)

    interestRate = 0

    def __init__(self, startingAmount, index):
        self._index = index

        if(startingAmount > 0):
            self._balance = startingAmount
            t = Transaction(date.today(), self._balance, False)
            self._transactions.append(t)
        else:
            self._balance = 0
            t = Transaction(date.today(), self._balance, False)
            sel._transactions.append(t)

        self._lastInterest = None
        logging.debug("Created transaction: " + str(self._index) + ", " + str(self._balance))

    def addTransaction(self, transaction, limit):
        """
        Applies a Transaction object to this account.
        transaction - Transaction object to be applied, specifies date, amount, and type of transaction
        limit - a boolean value (0 or 1). Determines whether account limits are to be applied (1), possibly preventing the transaction
        """
        if((transaction._amount + self._balance) >= 0 and limit == 1):
            if(transaction._dt < self._transactions[len(self._transactions) - 1]._dt):
                raise TransactionSequenceError(self._transactions[len(self._transactions) - 1]._dt)

            self._balance += transaction._amount
            self._transactions.append(transaction)
            self._transactions.sort(key = lambda x: x._dt)
        elif (limit == 1 and (transaction._amount + self._balance) < 0):
            raise OverdrawError

        if(limit == 0):
            self._balance += transaction._amount
            self._transactions.append(transaction)
            self._transactions.sort(key = lambda x: (x._dt, x._tme))
            self._lastInterest = transaction

        logging.debug("Created transaction: " + str(self._index) + ", " + str(transaction._amount))



    def addInterest(self):
        """
        Applies interest on balance according to respective account types.
        Requires date of interest application as a parameter
        """
        NotImplementedError()

    def printAccount(self):
        """
        Prints the name and balance of this account onto standard output.
        """
        NotImplementedError()

    def toString(self):
        """
        Returns as string the value of what would be printed under printAccount()
        """
        NotImplementedError()


class CheckingAccount(Account):
    
    interestRate = Decimal("0.0012") #interest rate for checking accounts

    def printAccount(self):
        print("Checking#%09d" % self._index + ",	balance: ${0:,.2f}".format(self._balance))

    def toString(self):
        return "Checking#%09d" % self._index + ",	balance: ${0:,.2f}".format(self._balance)

    def addInterest(self):
        intDate = self._transactions[len(self._transactions) - 1]._dt
        nextMonth = intDate.replace(day = 28) + timedelta(days=4)
        res = nextMonth - timedelta(days=nextMonth.day)

        #This checks for duplicate interest fees
        if not self._lastInterest == None: 
            if (self._lastInterest._dt == res):
                raise TransactionSequenceError(self._lastInterest._dt)

        self.addTransaction(Transaction(res, CheckingAccount.interestRate * self._balance, True), 0)
        if(self._balance < 100):
            self.addTransaction(Transaction(res, Decimal("-10"), True), 0)


class SavingsAccount(Account):

    interestRate = Decimal("0.029") #interest rate for savings accounts

    def printAccount(self):
        print("Savings#%09d" % self._index + ",	balance: ${0:,.2f}".format(self._balance))

    def toString(self):
        return "Savings#%09d" % self._index + ",	balance: ${0:,.2f}".format(self._balance)

    def addTransaction(self, transaction, limit):
        
        if(transaction._dt < self._transactions[len(self._transactions) - 1]._dt):
            raise TransactionSequenceError(self._transactions[len(self._transactions) - 1]._dt)
            return
        
        if(limit == 1):
            #check if transaction is fine
            if(transaction._amount + self._balance >= 0):
                dtNumber = 1
                monthNumber = 1
                for t in self._transactions:
                    if(not t._auto):
                        if (transaction._dt == t._dt):
                            dtNumber += 1
                        if(transaction._dt.month == t._dt.month):
                            monthNumber += 1
                        
                if(dtNumber <= 2 and monthNumber <= 5):
                    self._balance += transaction._amount
                    self._transactions.append(transaction)
                    self._transactions.sort(key = lambda x: (x._dt, x._tme))
                else:
                    raise TransactionLimitError(dtNumber <= 2)
            else:
                raise OverdrawError
                print("This transaction could not be completed due to an insufficient account balance.")
        else:
            self._balance += transaction._amount
            self._transactions.append(transaction)
            self._transactions.sort(key = lambda x: (x._dt, x._tme))
            self._lastInterest = transaction
        
        logging.debug("Created transaction: " + str(self._index) + ", " + str(transaction._amount))

    
    def addInterest(self):
        intDate = self._transactions[len(self._transactions) - 1]._dt
        nextMonth = intDate.replace(day = 28) + timedelta(days=4)
        res = nextMonth - timedelta(days=nextMonth.day)

        #This checks for duplicate interest fees
        if not self._lastInterest == None: 
            if (self._lastInterest._dt == res):
                raise TransactionSequenceError(self._lastInterest._dt)
                 
        self.addTransaction(Transaction(res, SavingsAccount.interestRate * self._balance, True), 0)


class Transaction(Base):

    __tablename__ = "transaction"
    _id = Column(Integer, primary_key = True)
    _account_idx = Column(Integer, ForeignKey("account._index"))
    _dt = Column(DateTime)
    _amount = Column(Float)
    _auto = Column(Boolean)
    _tme = Column(Time)

    def __init__(self, dt, amount, automatic):
        """
        Creates instance of Transaction class
        dt - date of transaction (as string)
        amount - amount of transaction
        automatic - True if this transaction was the result of automatic interest or fees. False otherwise (direct deposit/withdrawal).
        """
        self._dt = dt
        self._amount = amount
        self._auto = automatic
        self._tme = time.process_time()

    def printTransaction(self):
        """
        Prints the transaction as a string onto standard output.
        """
        print(self._dt.strftime("%Y-%m-%d") + ", ${0:,.2f}".format(self._amount))

    def toString(self):
        """
        Prints the transaction as a string onto standard output.
        """
        return self._dt.strftime("%Y-%m-%d") + ", ${0:,.2f}".format(self._amount)

class OverdrawError(Exception):
    "Raised when more money than in account is attempted to be withdrawn"
    pass

class TransactionSequenceError(Exception):
    "Raised when a transaction is made with a date before the last date"
    def __init__(self, lastDate):
        self.lastDate = lastDate
    pass

class TransactionLimitError(Exception):
    "Raised when attempted transaction fails transaction limit requirements"
    def __init__(self, isMonthError):
        if isMonthError:
            self.error = "5 transactions in this month."
        else:
            self.error = "2 transactions in this day."
    pass

logging.basicConfig(format = '%(asctime)s|%(levelname)s|%(message)s', datefmt = '%Y-%m-%d %I:%M:%S', filename = "bank.log", level=logging.DEBUG)

if __name__ == "__main__":
    try:
        BankCLI.run()
    except Exception as e:
        print("Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
        logging.error(repr(e))


