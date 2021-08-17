#!/bin/sh

setup_git() {
    git config --global user.email "bot@github.com"
    git config --global user.name "GitHub Bot"
}

git_commit_members_and_diffs() {
    git diff --stat
    git diff --shortstat members.tsv
    
    git add members.tsv
    git add diffs/*.txt
    git commit --message $(date +'%Y-%m-%d')" automatic update"
}

git_push() {
    # git checkout -b main
    git remote remove origin
    git remote add origin https://${GITHUB_ACTOR}:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git
    git push origin HEAD
}

prepare_diffs() {
    # git show HEAD:members.tsv > members_old.tsv
    # diff --strip-trailing-cr -U 0 members_old.tsv members.tsv > diffs/latest
    git diff -U0 members.tsv > diffs/full
    # tail -n +2 members.tsv | cut -f 2 | sort -u | sed 's/^$/ЦИК/' | xargs -I {} bash -c 'grep "$1" diffs/full > diffs/"$1".txt' -- {}
    # tail -n +2 members.tsv | cut -f 2 | sort -u | xargs -I {} bash -c 'grep "$1" diffs/full > diffs/"$1".txt' -- {}
    
    # grep -v '@@' diffs/full | awk -F'\t' 'NF>4&&$2=="ТИК № 21"{print $0}' | head
    
    tail -n +2 members.tsv | cut -f 2 | sort -u | sed 's/^$/ЦИК/' | xargs -I {} bash -c 'grep -v @@ diffs/full | awk -v var="$1" -F'"'"'\t'"'"' '"'"'NF>4&&($2==var||(var=="ЦИК"&&$2=="")){print $0}'"'"' > diffs/"$1".txt' -- {}
    ls -l diffs
    rm diffs/full
    find diffs -size 0 -print -delete
}

setup_git
git diff -s --exit-code members.tsv
ret_val=$?
if [ $ret_val -ne 0 ]; then
    prepare_diffs
    git_commit_members_and_diffs
    git_push
else
    echo "No changes found"
fi
wc members.tsv
