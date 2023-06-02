from sqlite3 import Row
import sys
import pickle
from tkinter import DoubleVar, StringVar, messagebox
from BankCLI import Bank, Account, CheckingAccount, SavingsAccount, Transaction, OverdrawError, TransactionSequenceError, TransactionLimitError
from datetime import datetime
from decimal import *

getcontext().rounding = ROUND_HALF_UP

import logging
logging.basicConfig(filename = 'bank.log', level = logging.DEBUG, format = "%(asctime)s|%(levelname)s|%(message)s", datefmt = "%Y-%m-%d %H:%M:%S")

import tkinter as tk
from tkinter import messagebox

class BankGUI:
    """Display a menu and respond to choices when run."""

    def __init__(self):
        self._window = tk.Tk()
        self._window.title("Premier Bank")
        self._options_frame = tk.Frame(self._window).grid(row=1, column=1)
        #self._window.report_callback_exception = self.handle_exception

        self._bank = Bank("Premier Bank")
        self._cur_account = None
        self._display_account = "None"

        # this label gets updated every time the selected account is changed
        self._display_line = tk.Label(self._options_frame, text="Currently selected account: " + self._display_account)
        self._display_line.grid(row=0, column=1, columnspan=4)

        tk.Button(self._options_frame, text="Open Account", command=self._create_account).grid(row=1, column=1)
        tk.Button(self._options_frame, text="Select Account", command=self._select_account).grid(row=1, column=2)
        tk.Button(self._options_frame, text="Add Transaction", command=self._create_transaction).grid(row=1, column=3)
        tk.Button(self._options_frame, text="Interest and Fees", command=self._add_interest).grid(row=1, column=4)
        tk.Button(self._options_frame, text="Save", command=self._save).grid(row=1, column=5)
        tk.Button(self._options_frame, text="Load", command=self._load).grid(row=1, column=6)

        self._list_frame = tk.Frame(self._window)
        self._list_frame.grid(row=3, column=1, columnspan=1, sticky="w")
        self._transaction_frame = tk.Frame(self._window)
        self._transaction_frame.grid(row=3, column=2, columnspan=1)
        self._entry_frame = tk.Frame(self._window)
        self._entry_frame.grid(row=2, column=1)

        self._window.mainloop()

    def _update_display(self):
        """Updates the displayed accounts every time one is added or selected."""

        accounts = self._bank._accounts

        row = 0

        # every cycle of updating the display, check if the accounts to display exist in the list to display, and if not put in an entry for it
        # destroy and rebuild the list every time because I can't be bothered finding out how to tie the account to the corresponding StringVar
        for x in self._list_frame.winfo_children():
            x.destroy()

        for x in accounts:
            tk.Label(self._list_frame, text=x.toString()).grid(row=row, column=1)
            row += 1          

        if self._cur_account != None:
            self._show_transactions(self._cur_account)

            self._display_account = self._cur_account.toString()
            self._display_line.destroy()
            self._display_line = tk.Label(self._options_frame, text="Currently selected account: " + self._display_account)
            self._display_line.grid(row=0, column=1, columnspan=4)

    def _create_account(self):
        """Creates a checking/savings account with an initial balance provided by the user."""

        # actually creates the account with the information inputted in the entry boxes
        def create_callback():
            try:
                initial_deposit = Decimal(initial_deposit_entry.get())
            except (TypeError, InvalidOperation):
                messagebox.showwarning(title="Invalid Dollar Amount", message="Please try again with a valid dollar amount.")

            account_type = account_type_entry.get()

            try:
                self._bank.addAccount(account_type == "checking", initial_deposit)
                logging.debug(f"Created account: {self._bank._accounts[-1]._index}")
                logging.debug(f"Created transaction: {self._bank._accounts[-1]._index}, {initial_deposit}")
            except OverdrawError:
                messagebox.showwarning(title="Invalid Dollar Amount", message="You cannot open an account with a negative balance.")

            account_type_label.destroy()
            account_type_entry.destroy()
            initial_deposit_label.destroy()
            initial_deposit_entry.destroy()
            enter.destroy()

            self._update_display()
        
        amount_checker = tk.StringVar()
        type_checker = tk.StringVar()

        # observes the input of amount_entry and colors an invalid input red
        def num_checker(var, index, mode):
            try:
                Decimal(amount_checker.get())
                initial_deposit_entry.configure(foreground="green")
            except (TypeError, InvalidOperation):
                initial_deposit_entry.configure(foreground="red")
        
        def account_checker(var, index, mode):
            if type_checker.get() == "checking" or type_checker.get() == "savings":
                account_type_entry.configure(foreground="green")
            else:
                account_type_entry.configure(foreground="red")

        amount_checker.trace_add("write", num_checker)
        type_checker.trace_add("write", account_checker)

        account_type_label = tk.Label(self._entry_frame, text="Type of Account:")
        account_type_label.grid(row=1, column=1)
        account_type_entry = tk.Entry(self._entry_frame, textvariable=type_checker)
        account_type_entry.grid(row=2, column=1)

        initial_deposit_label = tk.Label(self._entry_frame, text="Initial Deposit Amount:")
        initial_deposit_label.grid(row=1, column=2)
        initial_deposit_entry = tk.Entry(self._entry_frame, textvariable=amount_checker)
        initial_deposit_entry.grid(row=2, column=2)

        enter = tk.Button(self._entry_frame, text="Enter", command=create_callback)
        enter.grid(row=2, column=3)
    
    def _select_account(self):
        """Selects an account to view to add/view transactions for."""

        # once an account is selected, update the displayed account and destroy the extra window
        def create_callback(account):
            self._cur_account = account
            self._display_account = str(account)

            account_window.destroy()
            self._display_line["text"] = "Currently selected account: " + self._display_account
            self._show_transactions(account)

        account_window = tk.Tk()
        account_window.title("Select Account")
        account_frame = tk.Frame(account_window)
        account_frame.grid(row=1, column=1)
        row = 1

        for x in self._bank._accounts:
            button_text = x.toString()
            tk.Button(account_frame, text=str(button_text), command=lambda c=x: create_callback(c)).grid(row=row, column=1)
            row += 1

    def _show_transactions(self, account):
        """Displays all transactions for an account, sorted by date."""
        row = 0

        for x in self._transaction_frame.winfo_children():
            x.destroy() 

        for x in account._transactions:
            transaction = tk.Label(self._transaction_frame, text=x.toString(), anchor="e")
            transaction.grid(row=row, column=1)
            # green text for positive transactions, red for negative
            if x._amount >= 0:
                transaction.configure(foreground="green")
            else:
                transaction.configure(foreground="red")
            row += 1

    def _create_transaction(self):
        """Creates a Transaction object in the currently selected account and updates balance."""

        try:
            if self._cur_account == None:
                raise AttributeError

            def create_callback(account):
                try:
                    amount = Decimal(amount_entry.get())
                except (TypeError, InvalidOperation):
                    messagebox.showwarning(title="Invalid Dollar Amount", message="Please try again with a valid dollar amount.")

                try:
                    day = datetime.strptime(date_entry.get(), "%Y-%m-%d")

                    account.addTransaction(Transaction(day.date(), amount, False), 1)
                    logging.debug(f"Created transaction: {self._cur_account._index}, {amount}")
                except ValueError:
                    messagebox.showwarning(title="Invalid Date Format", message="Please try again with a valid date in the form YYYY-MM-DD.")
                except OverdrawError:
                    messagebox.showwarning(title="Invalid Withdrawl Amount", message="You cannot withdraw more than the account balance.")
                except TransactionLimitError:
                    messagebox.showwarning(title="Transaction Limit Reached", message="This account has reached a transaction limit.")
                except TransactionSequenceError as e:
                    messagebox.showwarning(title="Invalid Transaction Order", message="New transactions must be from {0} onward.".format(e.lastDate.isoformat()))

                amount_label.destroy()
                amount_entry.destroy()
                date_label.destroy()
                date_entry.destroy()
                enter.destroy()

                self._update_display()
                self._show_transactions(account)

            amount_checker = tk.StringVar()
            date_checker = tk.StringVar()

            # observes the input of amount_entry and colors an invalid input red
            def num_checker(var, index, mode):
                try:
                    Decimal(amount_checker.get())
                    amount_entry.configure(foreground="green")
                except (TypeError, InvalidOperation):
                    amount_entry.configure(foreground="red")

            def day_checker(var, index, mode):
                try:
                    datetime.strptime(date_checker.get(), "%Y-%m-%d")
                    date_entry.configure(foreground="green")
                except ValueError:
                    date_entry.configure(foreground="red")

            amount_checker.trace_add("write", num_checker)
            date_checker.trace_add("write", day_checker)
        
            amount_label = tk.Label(self._entry_frame, text="Amount:")
            amount_label.grid(row=1, column=1)
            amount_entry = tk.Entry(self._entry_frame, textvariable=amount_checker)
            amount_entry.grid(row=2, column=1)

            date_label = tk.Label(self._entry_frame, text="Date (YYYY-MM-DD):")
            date_label.grid(row=1, column=2)
            date_entry = tk.Entry(self._entry_frame, textvariable=date_checker)
            date_entry.grid(row=2, column=2)

            enter = tk.Button(self._entry_frame, text="Enter", command=lambda c=self._cur_account: create_callback(c))
            enter.grid(row=2, column=3)

        except AttributeError:
            messagebox.showwarning(title="Warning", message="You need to select an account first")
            
    def _add_interest(self):
        """Calculates the interest for an account depending on the type of the account and applies it to the account balance."""

        try:
            if self._cur_account == None:
                raise AttributeError

            try:
                fee_charged = self._cur_account.addInterest()

                if fee_charged:
                    logging.debug(f"Created transaction: {self._cur_account._index}, {self._cur_account._transactions[-2]._amount}")
                    logging.debug(f"Created transaction: {self._cur_account._index}, {self._cur_account._transactions[-1]._amount}")
                else:
                    logging.debug(f"Created transaction: {self._cur_account._index}, {self._cur_account._transactions[-1]._amount}")
                logging.debug("Triggered fees and interest")

                self._update_display()
                self._show_transactions(self._cur_account)

            except TransactionSequenceError as e:
                messagebox.showwarning(title="Already Applied Interest", message="Cannot apply interest and fees again in the month of {0}.".format(e.lastDate.strftime("%B")))

        except AttributeError as e:
            print(repr(e))
            messagebox.showwarning(title="Warning", message="You need to select an account first")

    def _save(self):
        with open("bank.pickle", "wb") as f:
            pickle.dump(self._bank, f)

        logging.debug("Saved to bank.pickle")

    def _load(self):
        with open("bank.pickle", "rb") as f:   
            self._bank = pickle.load(f)

        logging.debug("Loaded from bank.pickle")

    def handle_exception(self, exception, value, traceback):
        """Handles all exceptions that have not already been handled with other warning messages"""

        messagebox.showerror(title="Something went wrong!", message="Please contact our support team if the problem persists.")
        logging.error(f"{exception.__name__}: {repr(value)}")
        sys.exit(1)

if __name__ == "__main__":
    BankGUI()
    

if __name__ == "__main__":
    gui = BankGUI()