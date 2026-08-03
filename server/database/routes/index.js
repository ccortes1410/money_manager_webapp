const express = require('express');
const buildCrudRouter = require('./crud');
const db = require('../models');

const router = express.Router();

router.use('/transactions', buildCrudRouter(db.Transaction));
router.use('/budgets', buildCrudRouter(db.Budget));
router.use('/subscriptions', buildCrudRouter(db.Subscription, {
    include: [{ model: db.SubscriptionPayment, as: 'payments' }],
}));
router.use('/subscription-payments', buildCrudRouter(db.SubscriptionPayment));
router.use('/incomes', buildCrudRouter(db.Income));
router.use('/shared-budgets', buildCrudRouter(db.SharedBudget, {
    include : [{ model: db.SharedBudgetMember, as: 'members' }],
}));
router.use('/shared-budget-members', buildCrudRouter(db.SharedBudgetMember));
router.use('/shared-budget-invites', buildCrudRouter(db.SharedBudgetInvite));
router.use('/shared-expenses', buildCrudRouter(db.SharedExpense, {
    include: [{ model: db.ExpenseSplit, as: 'splits' }],
}));
router.use('/expense-splits', buildCrudRouter(db.ExpenseSplit));
router.use('/settlements', buildCrudRouter(db.Settlement));
router.use('/shared-budget-notifications', buildCrudRouter(db.SharedBudgetNotification));
router.use('/friendships', buildCrudRouter(db.Friendship));
router.use('/friendship-notifications', buildCrudRouter(db.FriendshipNotification));

module.exports = router;