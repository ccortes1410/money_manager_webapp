const sequelize = require('./db');
const User = require('./user');
const Transaction = require('./transaction');
const Budget = require('./budget');
const Subscription = require('./subscription');
const SubscriptionPayment = require('./subscriptionPayment');
const Income = require('./income');
const SharedBudget = require('./sharedBudget');
const SharedBudgetMember = require('./sharedBudgetMember');
const SharedBudgetInvite = require('./sharedBudgetInvite');
const SharedExpense = require('./sharedExpense');
const ExpenseSplit = require('./expenseSplit');
const Settlement = require('./settlement');
const SharedBudgetNotification = require('./sharedBudgetNotification');
const Friendship = require('./friendship');
const FriendshipNotification = require('./friendshipNotification');

// --- Associations (mirrors the ForeignKeys in djangoapp/models.models.py
// and djangoapp/models/friendship.py) ---

Transaction.belongsTo(User, { foreignKey: 'user_id' });
Budget.belongsTo(User, { foreignKey: 'user_id' });
Subscription.belongsTo(User, { foreignKey: 'user_id' });

Subscription.hasMany(SubscriptionPayment, { foreignKey: 'subscription_id', as: 'payments' });
SubscriptionPayment.belongsTo(Subscription, { foreignKey: 'subscription_id', as: 'subscription' });

Income.belongsTo(User, { foreignKey: 'user_id' });

SharedBudget.belongsTo(User, { foreignKey: 'created_by_id', as: 'creator' });
SharedBudget.hasMany(SharedBudgetMember, { foreignKey: 'shared_budget_id', as: 'members' });
SharedBudgetMember.belongsTo(SharedBudget, { foreignKey: 'shared_budget_id', as: 'sharedbudget' });
SharedBudgetMember.belongsTo(User, { foreignKey: 'user_id' });

SharedBudgetInvite.belongsTo(SharedBudget, { foreignKey: 'shared_budget_id', as: 'sharedBudget' });
SharedBudgetInvite.belongsTo(User, { foreignKey: 'invited_by_id', as: 'invitedBy' });
SharedBudgetInvite.belongsTo(User, { foreignKey: 'invited_user_id', as: 'invitedUser' });

SharedBudget.hasMany(SharedExpense, { foreignKey: 'shared_budget_id', as: 'expenses' });
SharedExpense.belongsTo(SharedBudget, { foreignKey: 'shared_budget_id', as: 'sharedBudget' });
SharedExpense.belongsTo(User, { foreignKey: 'paid_by_id', as: 'paidBy' });
SharedExpense.belongsTo(User, { foreignKey: 'created_by_id', as: 'createdBy' });

SharedExpense.hasMany(ExpenseSplit, { foreignKey: 'shared_expense_id', as: 'splits' });
ExpenseSplit.belongsTo(SharedExpense, { foreignKey: 'shared_expense_id', as: 'sharedExpense' });
ExpenseSplit.belongsTo(User, { foreignKey: 'user_id' });

Settlement.belongsTo(SharedBudget, { foreignKey: 'shared_budget_id', as: 'sharedBudget' });
Settlement.belongsTo(User, { foreignKey: 'payer_id', as: 'payer' });
Settlement.belongsTo(User, { foreignKey: 'receiver_id', as: 'receiver' });

SharedBudgetNotification.belongsTo(User, { foreignKey: 'user_id' });
SharedBudgetNotification.belongsTo(User, { foreignKey: 'from_user_id', as: 'fromUser' });
SharedBudgetNotification.belongsTo(SharedBudget, { foreignKey: 'shared_budget_id', as: 'sharedBudget' });

Friendship.belongsTo(User, { foreignKey: 'sender_id', as: 'sender' });
Friendship.belongsTo(User, { foreignKey: 'receiver_id', as: 'receiver' });

FriendshipNotification.belongsTo(User, { foreignKey: 'user_id' });
FriendshipNotification.belongsTo(User, { foreignKey: 'from_user_id', as: 'fromUser' });
FriendshipNotification.belongsTo(Friendship, { foreignKey: 'friendship_id', as: 'friendship' });

module.exports = {
    sequelize,
    User,
    Transaction,
    Budget,
    Subscription,
    SubscriptionPayment,
    Income,
    SharedBudget,
    SharedBudgetMember,
    SharedBudgetInvite,
    SharedExpense,
    ExpenseSplit,
    Settlement,
    SharedBudgetNotification,
    Friendship,
    FriendshipNotification,
}